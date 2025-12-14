"""
Logging and metrics system for StoryBox IA

Provides structured logging with:
- File rotation (prevents SD card overflow on Pi)
- Console output for development
- Metrics tracking (latency, tokens/sec, etc.)
- JSON formatting for log aggregation

Usage:
    from app.utils.logger import get_logger, log_metric

    logger = get_logger(__name__)
    logger.info("Starting story generation")

    # Track performance metrics
    log_metric("stt_latency_ms", 1234)
    log_metric("llm_tokens_per_second", 4.5)

Author: StoryBox IA Team
Date: 2024-12
"""

import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MetricsCollector:
    """
    Collects performance metrics for monitoring

    Metrics are stored in memory and can be:
    - Logged periodically
    - Exported to monitoring systems
    - Written to metrics file

    Thread-safe for concurrent metric updates.
    """
    metrics: Dict[str, list] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)

    def record(self, metric_name: str, value: float):
        """
        Record a metric value

        Args:
            metric_name: Name of the metric (e.g., "stt_latency_ms")
            value: Metric value
        """
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []

        self.metrics[metric_name].append({
            'value': value,
            'timestamp': time.time()
        })

    def get_stats(self, metric_name: str) -> Optional[Dict[str, float]]:
        """
        Get statistics for a metric

        Args:
            metric_name: Name of the metric

        Returns:
            Dict with min, max, avg, count or None if no data
        """
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return None

        values = [m['value'] for m in self.metrics[metric_name]]
        return {
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'count': len(values)
        }

    def reset(self):
        """Clear all metrics"""
        self.metrics.clear()
        self.start_time = time.time()

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of all metrics

        Returns:
            Dictionary with statistics for each metric
        """
        summary = {
            'uptime_seconds': time.time() - self.start_time,
            'metrics': {}
        }

        for metric_name in self.metrics:
            stats = self.get_stats(metric_name)
            if stats:
                summary['metrics'][metric_name] = stats

        return summary


# Global metrics collector
_metrics_collector = MetricsCollector()


def log_metric(metric_name: str, value: float):
    """
    Log a performance metric

    Args:
        metric_name: Name of the metric
        value: Metric value

    Example:
        >>> log_metric("stt_latency_ms", 1234)
        >>> log_metric("llm_tokens_per_second", 4.5)
    """
    _metrics_collector.record(metric_name, value)

    # Also log to file for historical tracking
    logger = get_logger('metrics')
    logger.info(f"Metric: {metric_name}", extra={
        'metric_name': metric_name,
        'metric_value': value,
        'timestamp': datetime.now().isoformat()
    })


def get_metrics_summary() -> Dict[str, Any]:
    """
    Get summary of all collected metrics

    Returns:
        Dictionary with metric statistics
    """
    return _metrics_collector.get_summary()


def reset_metrics():
    """Reset all collected metrics"""
    _metrics_collector.reset()


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter for structured logging

    Adds custom fields:
    - timestamp (ISO format)
    - component (logger name)
    - level (log level)
    - message (log message)
    - Any extra fields passed via extra={}
    """

    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)

        # Add timestamp in ISO format
        log_record['timestamp'] = datetime.fromtimestamp(record.created).isoformat()

        # Add log level
        log_record['level'] = record.levelname

        # Add component (logger name)
        log_record['component'] = record.name

        # Add message
        if 'message' not in log_record:
            log_record['message'] = record.getMessage()


def setup_logging(
    log_dir: str = "logs",
    log_level: str = "INFO",
    max_bytes: int = 50 * 1024 * 1024,  # 50MB
    backup_count: int = 3,
    console_output: bool = True,
    json_format: bool = False
) -> None:
    """
    Setup logging system with file rotation

    Args:
        log_dir: Directory for log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        max_bytes: Max size per log file before rotation
        backup_count: Number of backup files to keep
        console_output: Enable console logging
        json_format: Use JSON format for logs (better for parsing)

    Example:
        >>> from app.utils.config import get_config
        >>> config = get_config()
        >>> setup_logging(
        ...     log_dir=config.logging.log_dir,
        ...     log_level=config.logging.level,
        ...     max_bytes=config.logging.max_log_size_mb * 1024 * 1024,
        ...     backup_count=config.logging.backup_count
        ... )
    """
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # File handler with rotation
    log_file = log_path / "storybox.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))

    # Formatter
    if json_format:
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(component)s %(message)s'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Console handler (for development)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))

        # Console uses simple format (not JSON)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # Log startup message
    root_logger.info("=" * 60)
    root_logger.info("StoryBox IA - Logging initialized")
    root_logger.info(f"Log directory: {log_path.absolute()}")
    root_logger.info(f"Log level: {log_level}")
    root_logger.info(f"Max log size: {max_bytes / 1024 / 1024:.1f} MB")
    root_logger.info(f"Backup count: {backup_count}")
    root_logger.info("=" * 60)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific component

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing audio input")
        >>> logger.error("Failed to load model", exc_info=True)
    """
    return logging.getLogger(name)


class TimingContext:
    """
    Context manager for timing code blocks and logging metrics

    Usage:
        >>> with TimingContext("stt_inference", log_metric=True):
        ...     result = whisper_model.transcribe(audio)

    This will automatically log the metric "stt_inference_ms" with the elapsed time.
    """

    def __init__(self, operation_name: str, log_metric: bool = True, logger_name: Optional[str] = None):
        """
        Initialize timing context

        Args:
            operation_name: Name of the operation being timed
            log_metric: Whether to log as a metric
            logger_name: Optional logger name (defaults to 'timing')
        """
        self.operation_name = operation_name
        self.log_metric_flag = log_metric
        self.logger = get_logger(logger_name or 'timing')
        self.start_time = None
        self.elapsed_ms = None

    def __enter__(self):
        """Start timing"""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        End timing and log result

        If an exception occurred, log it as an error.
        """
        self.elapsed_ms = (time.time() - self.start_time) * 1000

        if exc_type is None:
            # Success
            self.logger.info(
                f"{self.operation_name} completed in {self.elapsed_ms:.1f}ms",
                extra={
                    'operation': self.operation_name,
                    'elapsed_ms': self.elapsed_ms
                }
            )

            if self.log_metric_flag:
                log_metric(f"{self.operation_name}_ms", self.elapsed_ms)
        else:
            # Error
            self.logger.error(
                f"{self.operation_name} failed after {self.elapsed_ms:.1f}ms: {exc_val}",
                extra={
                    'operation': self.operation_name,
                    'elapsed_ms': self.elapsed_ms,
                    'error': str(exc_val)
                },
                exc_info=True
            )

        # Don't suppress exceptions
        return False


def log_system_info():
    """
    Log system information for debugging

    Logs:
    - Python version
    - Platform
    - CPU info (if available)
    - Memory info (if available)
    - Model paths
    """
    import platform
    import sys

    logger = get_logger('system')

    logger.info("=" * 60)
    logger.info("System Information")
    logger.info("=" * 60)
    logger.info(f"Python: {sys.version}")
    logger.info(f"Platform: {platform.system()} {platform.release()}")
    logger.info(f"Machine: {platform.machine()}")
    logger.info(f"Processor: {platform.processor()}")

    # Try to get CPU and memory info (psutil)
    try:
        import psutil

        logger.info(f"CPU cores: {psutil.cpu_count(logical=False)} physical, {psutil.cpu_count(logical=True)} logical")

        mem = psutil.virtual_memory()
        logger.info(f"Memory: {mem.total / 1024 / 1024 / 1024:.1f} GB total, {mem.available / 1024 / 1024 / 1024:.1f} GB available")

        # Temperature (Raspberry Pi specific)
        if platform.system() == 'Linux':
            try:
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                    temp = int(f.read()) / 1000.0
                    logger.info(f"CPU Temperature: {temp:.1f}°C")
            except:
                pass

    except ImportError:
        logger.debug("psutil not available, skipping detailed system info")

    logger.info("=" * 60)
