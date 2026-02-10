from logging import WARNING
from typing import Optional

import httpx
from httpx import Response
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    retry_if_exception_type,
    retry_if_result,
    after_log, wait_random,
)


class HTTPManager:
    """HTTP Manager that implements all request logic internally."""

    @classmethod
    async def execute_request(
        cls,
        url: str,
        method: str = "GET",
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        headers: Optional[dict] = None,
        json: Optional[dict] = None,
        cookies: Optional[dict] = None,
        follow_redirects: bool = False,
        timeout: Optional[int] = 30,
    ) -> Optional[Response]:
        """
        Execute HTTP request - contains all the logic from send_request body.
        This method implements the actual request logic internally.
        """

        proxy = None

        if headers is None:
            headers = {"User-Agent": ua.random}
        else:
            headers = headers.copy()
        headers["User-Agent"] = ua.random

        async with httpx.AsyncClient(
            proxy=proxy,
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
