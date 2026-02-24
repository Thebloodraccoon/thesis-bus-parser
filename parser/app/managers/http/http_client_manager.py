import os
import traceback
from logging import WARNING
from typing import Optional

import httpx
from httpx import Response
from httpx._transports.default import AsyncHTTPTransport
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    retry_if_exception_type,
    retry_if_result,
    after_log,
    wait_random,
)

from parser.app.managers.http.proxy import ProxyManager
from parser.app.settings.conf import ua


def get_response_size(response):
    """Get response size in kilobytes."""
    actual_body_size = len(response.content)
    compressed_size = response.headers.get("x-compressed-size")

    if compressed_size:
        total_compressed_kb = int(compressed_size) / 1024
    else:
        total_compressed_kb = actual_body_size / 1024

    return round(total_compressed_kb, 2)


def calculate_headers_size(response):
    """Calculate headers size."""
    status_line = (
        f"HTTP/1.1 {response.status_code} {response.reason_phrase or 'OK'}\r\n"
    )
    headers_text = status_line.encode("utf-8")

    for name, value in response.headers.items():
        header_line = f"{name}: {value}\r\n"
        headers_text += header_line.encode("utf-8")

    headers_text += b"\r\n"
    return len(headers_text)


class CompressionTrackingTransport(AsyncHTTPTransport):
    """Transport for tracking HTTP response size."""

    def __init__(self, proxy: str = None):
        super().__init__(proxy=proxy)

    async def handle_async_request(self, request):
        """Handle async request with size tracking."""
        response = await super().handle_async_request(request)

        try:
            if hasattr(response, "stream"):
                raw_content = b""
                async for chunk in response.stream:
                    raw_content += chunk

                body_size = len(raw_content)
                headers_size = calculate_headers_size(response)
                total_size = headers_size + body_size

                new_response = Response(
                    status_code=response.status_code,
                    headers=response.headers,
                    content=raw_content,
                    request=request,
                )

                new_response.headers["X-Compressed-Size"] = str(total_size)
                return new_response
            else:
                return response

        except Exception:
            return response


class HTTPManager:
    """HTTP Manager that implements all request logic internally."""

    def __init__(self, use_proxy: bool = True):
        self.use_proxy = use_proxy
        self._current_proxy = None

    async def execute_request(
        self,
        url: str,
        method: str = "GET",
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        headers: Optional[dict] = None,
        json: Optional[dict] = None,
        cookies: Optional[dict] = None,
        follow_redirects: bool = False,
        timeout: int = 30,
    ) -> Optional[Response]:
        """
        Execute HTTP request - contains all the logic from send_request body.
        This method implements the actual request logic internally.
        """

        proxy = ProxyManager().get_proxy() if self.use_proxy else None
        self._current_proxy = proxy

        if headers is None:
            headers = {"User-Agent": ua.random}
        else:
            headers = headers.copy()
        headers["User-Agent"] = ua.random

        transport = CompressionTrackingTransport(proxy=proxy)
        async with httpx.AsyncClient(
            transport=transport,
            timeout=timeout,
            cookies=cookies,
            follow_redirects=follow_redirects,
        ) as client:
            if method.upper() == "GET":
                response = await client.get(url, params=params, headers=headers)
            elif method.upper() == "POST":
                response = await client.post(
                    url, params=params, data=data, json=json, headers=headers
                )
            else:
                raise httpx.HTTPError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response

    @classmethod
    async def upload_file(
        cls,
        url: str,
        file_path: str,
        field_name: str = "file",
        additional_data: Optional[dict] = None,
        headers: Optional[dict] = None,
        timeout: int = 60,
    ) -> Optional[Response]:
        """Upload file using multipart/form-data."""

        if headers is None:
            headers = {"User-Agent": ua.random}
        else:
            headers = headers.copy()
            headers["User-Agent"] = ua.random

        try:
            async with httpx.AsyncClient(
                timeout=timeout, verify=False, follow_redirects=True
            ) as client:
                with open(file_path, "rb") as f:
                    file_name = os.path.basename(file_path)

                    files = {field_name: (file_name, f, "text/csv")}
                    data = additional_data or {}

                    response = await client.post(
                        url, files=files, data=data, headers=headers
                    )
                    response.raise_for_status()
                    return response

        except Exception as e:
            logger.error(f"Unexpected error: {type(e).__name__}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise


# Global instance for backward compatibility
http_manager = HTTPManager()


@retry(
    stop=stop_after_attempt(10),
    wait=wait_random(min=0.2, max=2),
    retry=(
        retry_if_exception_type(
            (
                httpx.RequestError,
                httpx.HTTPStatusError,
                httpx.TimeoutException,
                httpx.ConnectError,
                httpx.ProxyError,
                httpx.RemoteProtocolError,
                httpx.ReadTimeout,
                httpx.WriteTimeout,
                httpx.ReadError,
            )
        )
        | retry_if_result(
            lambda result: result is not None and result.status_code == 502
        )
    ),
    after=after_log(logger, log_level=WARNING),
    reraise=True,
)
async def send_request(
    url: str,
    method: str = "GET",
    params: Optional[dict] = None,
    data: Optional[dict] = None,
    headers: Optional[dict] = None,
    json: Optional[dict] = None,
    cookies: Optional[dict] = None,
    follow_redirects: bool = False,
    timeout: int = 30,
) -> Optional[httpx.Response]:
    """
    Backward compatibility function with tenacity retry outside.
    Uses HTTPManager internally to execute the actual request logic.
    """
    return await http_manager.execute_request(
        url=url,
        method=method,
        params=params,
        data=data,
        headers=headers,
        json=json,
        cookies=cookies,
        follow_redirects=follow_redirects,
        timeout=timeout,
    )
