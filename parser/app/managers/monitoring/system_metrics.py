from datetime import datetime
from typing import Dict, Any

import psutil
from prometheus_client import Gauge, Counter, Histogram, CollectorRegistry

from parser.app.settings.logger import get_logger
from .pushgateway_client import PushgatewayClient

logger = get_logger(__name__)


class SystemMetricsCollector:
    """The collector of system metrics for resource monitoring."""

    def __init__(self, job_name: str = "system_metrics"):
        self.job_name = job_name

        self.registry = CollectorRegistry()

        self.pushgateway_client = PushgatewayClient(job_name=job_name)
        self.pushgateway_client.registry = self.registry

        # System metric
        self.cpu_usage_percent = Gauge(
            "system_cpu_usage_percent",
            "CPU usage percentage",
            ["hostname"],
            registry=self.registry,
        )

        self.memory_usage_percent = Gauge(
            "system_memory_usage_percent",
            "Memory usage percentage",
            ["hostname"],
            registry=self.registry,
        )

        self.memory_available_gb = Gauge(
            "system_memory_available_gb",
            "Available memory in GB",
            ["hostname"],
            registry=self.registry,
        )

        self.memory_total_gb = Gauge(
            "system_memory_total_gb",
            "Total memory in GB",
            ["hostname"],
            registry=self.registry,
        )

        self.disk_usage_percent = Gauge(
            "system_disk_usage_percent",
            "Disk usage percentage",
            ["hostname", "mountpoint"],
            registry=self.registry,
        )

        self.disk_available_gb = Gauge(
            "system_disk_available_gb",
            "Available disk space in GB",
            ["hostname", "mountpoint"],
            registry=self.registry,
        )

        self.disk_total_gb = Gauge(
            "system_disk_total_gb",
            "Total disk space in GB",
            ["hostname", "mountpoint"],
            registry=self.registry,
        )

        self.network_bytes_sent = Counter(
            "system_network_bytes_sent",
            "Network bytes sent",
            ["hostname", "interface"],
            registry=self.registry,
        )

        self.network_bytes_recv = Counter(
            "system_network_bytes_recv",
            "Network bytes received",
            ["hostname", "interface"],
            registry=self.registry,
        )

        self.load_average_1min = Gauge(
            "system_load_average_1min",
            "1-minute load average",
            ["hostname"],
            registry=self.registry,
        )

        self.load_average_5min = Gauge(
            "system_load_average_5min",
            "5-minute load average",
            ["hostname"],
            registry=self.registry,
        )

        self.load_average_15min = Gauge(
            "system_load_average_15min",
            "15-minute load average",
            ["hostname"],
            registry=self.registry,
        )

        # Meter to track the number of metric fees
        self.metrics_collection_count = Counter(
            "system_metrics_collection_total",
            "Total number of metrics collections",
            ["hostname"],
            registry=self.registry,
        )

        # Histogram for the time to collect metric
        self.metrics_collection_duration = Histogram(
            "system_metrics_collection_duration_seconds",
            "Time spent collecting system metrics",
            ["hostname"],
            registry=self.registry,
        )

        # We get the name of the host
        self.hostname = self._get_hostname()

        # Previous values for network meters
        self._prev_network_stats = {}

    @classmethod
    def _get_hostname(cls) -> str:
        """Receives the name of the host."""

        try:
            import socket

            return socket.gethostname()
        except Exception:
            return "unknown"

    def collect_cpu_metrics(self) -> Dict[str, Any]:
        """Collects CPU metrics."""

        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            load_avg = psutil.getloadavg()

            # Install metrics
            self.cpu_usage_percent.labels(hostname=self.hostname).set(cpu_percent)
            self.load_average_1min.labels(hostname=self.hostname).set(load_avg[0])
            self.load_average_5min.labels(hostname=self.hostname).set(load_avg[1])
            self.load_average_15min.labels(hostname=self.hostname).set(load_avg[2])

            return {
                "cpu_percent": cpu_percent,
                "load_1min": load_avg[0],
                "load_5min": load_avg[1],
                "load_15min": load_avg[2],
            }
        except Exception as e:
            logger.error(f"Failed to collect CPU metrics: {e}")
            return {}

    def collect_memory_metrics(self) -> Dict[str, Any]:
        """Collects memory metrics."""

        try:
            memory = psutil.virtual_memory()

            # We convert to GB
            total_gb = memory.total / (1024**3)
            available_gb = memory.available / (1024**3)

            # Install metrics
            self.memory_usage_percent.labels(hostname=self.hostname).set(memory.percent)
            self.memory_available_gb.labels(hostname=self.hostname).set(available_gb)
            self.memory_total_gb.labels(hostname=self.hostname).set(total_gb)

            return {
                "memory_percent": memory.percent,
                "memory_available_gb": available_gb,
                "memory_total_gb": total_gb,
                "memory_used_gb": (memory.total - memory.available) / (1024**3),
            }
        except Exception as e:
            logger.error(f"Failed to collect memory metrics: {e}")
            return {}

    def collect_disk_metrics(self) -> Dict[str, Any]:
        """Collects disks metrics."""

        try:
            disk_metrics = {}

            partitions = psutil.disk_partitions()

            for partition in partitions:
                try:
                    if partition.fstype in ["tmpfs", "devtmpfs", "sysfs", "proc"]:
                        continue

                    usage = psutil.disk_usage(partition.mountpoint)

                    total_gb = usage.total / (1024**3)
                    available_gb = usage.free / (1024**3)

                    self.disk_usage_percent.labels(
                        hostname=self.hostname, mountpoint=partition.mountpoint
                    ).set(usage.percent)

                    self.disk_available_gb.labels(
                        hostname=self.hostname, mountpoint=partition.mountpoint
                    ).set(available_gb)

                    self.disk_total_gb.labels(
                        hostname=self.hostname, mountpoint=partition.mountpoint
                    ).set(total_gb)

                    disk_metrics[partition.mountpoint] = {
                        "usage_percent": usage.percent,
                        "available_gb": available_gb,
                        "total_gb": total_gb,
                        "used_gb": (usage.total - usage.free) / (1024**3),
                    }

                except Exception as e:
                    logger.warning(
                        f"Failed to collect disk metrics for {partition.mountpoint}: {e}"
                    )
                    continue

            return disk_metrics

        except Exception as e:
            logger.error(f"Failed to collect disk metrics: {e}")
            return {}

    def collect_network_metrics(self) -> Dict[str, Any]:
        """Collects network metrics."""

        try:
            network_metrics = {}
            current_time = datetime.now()

            net_io = psutil.net_io_counters(pernic=True)
            for interface, stats in net_io.items():
                if interface.startswith("lo"):
                    continue

                prev_stats = self._prev_network_stats.get(
                    interface,
                    {"bytes_sent": 0, "bytes_recv": 0, "timestamp": current_time},
                )

                bytes_sent_diff = stats.bytes_sent - prev_stats["bytes_sent"]
                bytes_recv_diff = stats.bytes_recv - prev_stats["bytes_recv"]

                if bytes_sent_diff > 0:
                    self.network_bytes_sent.labels(
                        hostname=self.hostname, interface=interface
                    ).inc(bytes_sent_diff)

                if bytes_recv_diff > 0:
                    self.network_bytes_recv.labels(
                        hostname=self.hostname, interface=interface
                    ).inc(bytes_recv_diff)

                self._prev_network_stats[interface] = {
                    "bytes_sent": stats.bytes_sent,
                    "bytes_recv": stats.bytes_recv,
                    "timestamp": current_time,
                }

                network_metrics[interface] = {
                    "bytes_sent": stats.bytes_sent,
                    "bytes_recv": stats.bytes_recv,
                    "bytes_sent_diff": bytes_sent_diff,
                    "bytes_recv_diff": bytes_recv_diff,
                }

            return network_metrics

        except Exception as e:
            logger.error(f"Failed to collect network metrics: {e}")
            return {}

    def collect_all_metrics(self) -> Dict[str, Any]:
        """Collects all system metrics."""

        start_time = datetime.now()

        try:
            cpu_metrics = self.collect_cpu_metrics()
            memory_metrics = self.collect_memory_metrics()
            disk_metrics = self.collect_disk_metrics()
            network_metrics = self.collect_network_metrics()

            self.metrics_collection_count.labels(hostname=self.hostname).inc()

            duration = (datetime.now() - start_time).total_seconds()
            self.metrics_collection_duration.labels(hostname=self.hostname).observe(
                duration
            )

            self.pushgateway_client.push_metrics()

            all_metrics = {
                "cpu": cpu_metrics,
                "memory": memory_metrics,
                "disk": disk_metrics,
                "network": network_metrics,
                "collection_duration": duration,
            }

            logger.debug(f"System metrics collected in {duration:.3f}s: {all_metrics}")

            return all_metrics

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {}
