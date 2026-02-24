import asyncio
import socket
from datetime import datetime
from typing import Dict, Any

import aiohttp
import asyncpg
import redis.asyncio as redis
from prometheus_client import Gauge, Counter, CollectorRegistry

from .pushgateway_client import PushgatewayClient

from parser.app.settings.constants import settings
from parser.app.settings.logger import get_logger

logger = get_logger(__name__)


class ServiceHealthChecker:
    """Checking the health of services."""

    def __init__(self, job_name: str = "service_health"):
        self.job_name = job_name

        self.registry = CollectorRegistry()

        self.pushgateway_client = PushgatewayClient(job_name=job_name)
        self.pushgateway_client.registry = self.registry

        self.service_health_status = Gauge(
            "service_health_status",
            "Service health status (1=healthy, 0=unhealthy)",
            ["service_name", "service_type", "endpoint"],
            registry=self.registry,
        )

        self.service_response_time = Gauge(
            "service_response_time_seconds",
            "Service response time in seconds",
            ["service_name", "service_type", "endpoint"],
            registry=self.registry,
        )

        self.service_check_count = Counter(
            "service_health_check_total",
            "Total number of health checks",
            ["service_name", "service_type", "status"],
            registry=self.registry,
        )

        self.hostname = self._get_hostname()

    @classmethod
    def _get_hostname(cls) -> str:
        """Gets the hostname."""
        try:
            return socket.gethostname()
        except Exception:
            return "unknown"

    async def check_postgresql_health(self) -> Dict[str, Any]:
        """Checks the health of PostgreSQL."""
        results = {}

        try:
            start_time = datetime.now()
            conn = await asyncpg.connect(
                host=settings.POSTGRES_HOST,
                port=int(settings.POSTGRES_PORT),
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD.get_secret_value(),
                database=settings.POSTGRES_DB,
            )
            await conn.execute("SELECT 1")
            await conn.close()

            response_time = (datetime.now() - start_time).total_seconds()

            self.service_health_status.labels(
                service_name="prod_db",
                service_type="database",
                endpoint="localhost:5432",
            ).set(1)

            self.service_response_time.labels(
                service_name="prod_db",
                service_type="database",
                endpoint="localhost:5432",
            ).set(response_time)

            self.service_check_count.labels(
                service_name="prod_db", service_type="database", status="healthy"
            ).inc()

            results["prod_db"] = {
                "status": "healthy",
                "response_time": response_time,
                "type": "database",
            }

            logger.info(
                f"PostgreSQL prod_db: healthy (response time: {response_time:.3f}s)"
            )

        except Exception as e:
            self.service_health_status.labels(
                service_name="prod_db",
                service_type="database",
                endpoint="localhost:5432",
            ).set(0)

            self.service_check_count.labels(
                service_name="prod_db", service_type="database", status="unhealthy"
            ).inc()

            results["prod_db"] = {
                "status": "unhealthy",
                "error": str(e),
                "type": "database",
            }

            logger.warning(f"PostgreSQL prod_db: unhealthy - {e}")

        return results

    async def check_redis_health(self) -> Dict[str, Any]:
        """Checks Redis health."""
        results = {}

        try:
            start_time = datetime.now()

            r = redis.from_url(settings.REDIS_URL, decode_responses=True)

            await r.ping()
            await r.close()

            response_time = (datetime.now() - start_time).total_seconds()

            self.service_health_status.labels(
                service_name="redis", service_type="cache", endpoint="localhost:6379"
            ).set(1)

            self.service_response_time.labels(
                service_name="redis", service_type="cache", endpoint="localhost:6379"
            ).set(response_time)

            self.service_check_count.labels(
                service_name="redis", service_type="cache", status="healthy"
            ).inc()

            results["redis"] = {
                "status": "healthy",
                "response_time": response_time,
                "type": "cache",
            }

            logger.info(f"Redis: healthy (response time: {response_time:.3f}s)")

        except Exception as e:
            self.service_health_status.labels(
                service_name="redis", service_type="cache", endpoint="localhost:6379"
            ).set(0)

            self.service_check_count.labels(
                service_name="redis", service_type="cache", status="unhealthy"
            ).inc()

            results["redis"] = {"status": "unhealthy", "error": str(e), "type": "cache"}

            logger.warning(f"Redis: unhealthy - {e}")

        return results

    async def check_grafana_health(self) -> Dict[str, Any]:
        """Checks Grafana's health."""

        try:
            start_time = datetime.now()

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://172.17.0.1:3000/api/health", timeout=5
                ) as response:
                    if response.status == 200:
                        await response.json()
                        response_time = (datetime.now() - start_time).total_seconds()

                        self.service_health_status.labels(
                            service_name="grafana",
                            service_type="monitoring",
                            endpoint="localhost:3000",
                        ).set(1)

                        self.service_response_time.labels(
                            service_name="grafana",
                            service_type="monitoring",
                            endpoint="localhost:3000",
                        ).set(response_time)

                        self.service_check_count.labels(
                            service_name="grafana",
                            service_type="monitoring",
                            status="healthy",
                        ).inc()

                        logger.info(
                            f"Grafana: healthy (response time: {response_time:.3f}s)"
                        )

                        return {
                            "grafana": {
                                "status": "healthy",
                                "response_time": response_time,
                                "type": "monitoring",
                            }
                        }
                    else:
                        raise Exception(f"HTTP {response.status}")

        except Exception as e:
            self.service_health_status.labels(
                service_name="grafana",
                service_type="monitoring",
                endpoint="localhost:3000",
            ).set(0)

            self.service_check_count.labels(
                service_name="grafana", service_type="monitoring", status="unhealthy"
            ).inc()

            logger.warning(f"Grafana: unhealthy - {e}")

            return {
                "grafana": {
                    "status": "unhealthy",
                    "error": str(e),
                    "type": "monitoring",
                }
            }

    async def check_prometheus_health(self) -> Dict[str, Any]:
        """Checks the health of Prometheus."""

        try:
            start_time = datetime.now()

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://172.17.0.1:9090/-/healthy", timeout=5
                ) as response:
                    if response.status == 200:
                        response_time = (datetime.now() - start_time).total_seconds()

                        self.service_health_status.labels(
                            service_name="prometheus",
                            service_type="monitoring",
                            endpoint="localhost:9090",
                        ).set(1)

                        self.service_response_time.labels(
                            service_name="prometheus",
                            service_type="monitoring",
                            endpoint="localhost:9090",
                        ).set(response_time)

                        self.service_check_count.labels(
                            service_name="prometheus",
                            service_type="monitoring",
                            status="healthy",
                        ).inc()

                        logger.info(
                            f"Prometheus: healthy (response time: {response_time:.3f}s)"
                        )

                        return {
                            "prometheus": {
                                "status": "healthy",
                                "response_time": response_time,
                                "type": "monitoring",
                            }
                        }
                    else:
                        raise Exception(f"HTTP {response.status}")

        except Exception as e:
            self.service_health_status.labels(
                service_name="prometheus",
                service_type="monitoring",
                endpoint="localhost:9090",
            ).set(0)

            self.service_check_count.labels(
                service_name="prometheus", service_type="monitoring", status="unhealthy"
            ).inc()

            logger.warning(f"Prometheus: unhealthy - {e}")

            return {
                "prometheus": {
                    "status": "unhealthy",
                    "error": str(e),
                    "type": "monitoring",
                }
            }

    async def check_all_services(self) -> Dict[str, Any]:
        """Checks the health of all services."""
        start_time = datetime.now()

        try:
            tasks = [
                self.check_postgresql_health(),
                self.check_redis_health(),
                self.check_grafana_health(),
                self.check_prometheus_health(),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            all_results = {}
            for result in results:
                if isinstance(result, dict):
                    all_results.update(result)

            self.pushgateway_client.push_metrics()

            duration = (datetime.now() - start_time).total_seconds()

            healthy_services = len(
                [s for s in all_results.values() if s.get("status") == "healthy"]
            )
            total_services = len(all_results)

            logger.info(
                f"Service health check completed in {duration:.3f}s: "
                f"{healthy_services}/{total_services} managers healthy"
            )

            return {
                "managers": all_results,
                "summary": {
                    "total_services": total_services,
                    "healthy_services": healthy_services,
                    "unhealthy_services": total_services - healthy_services,
                    "check_duration": duration,
                },
            }

        except Exception as e:
            logger.error(f"Failed to check service health: {e}")
            return {
                "managers": {},
                "summary": {
                    "total_services": 0,
                    "healthy_services": 0,
                    "unhealthy_services": 0,
                    "check_duration": (datetime.now() - start_time).total_seconds(),
                    "error": str(e),
                },
            }
