import asyncio
import functools
import time
from typing import Any, Callable, Coroutine, TypeVar, Union

from prometheus_client import Counter, Histogram

from src.logger import logger

BUCKETS = [
    0.0001,
    0.001,
    0.01,
    0.02,
    0.05,
    0.1,
    0.2,
    0.4,
    0.6,
    0.8,
    1.0,
    1.2,
    1.4,
    1.6,
    1.8,
    2.0,
    float('+inf'),
]

LATENCY = Histogram(
    'latency_seconds',
    'Время выполнения операций',
    labelnames=['operation'],
    buckets=BUCKETS,
)

TOTAL_SEND_MESSAGES = Counter(
    'send_messages_total',
    'Количество отправленных сообщений',
    labelnames=['operation'],
)

T = TypeVar('T', bound=Union[Callable[..., Coroutine[Any, Any, Any]], Callable[..., Any]])


def measure_time(operation_name: str) -> Callable[[T], T]:
    def decorator(func: T) -> T:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                end_time = time.perf_counter()
                duration = end_time - start_time
                LATENCY.labels(operation=operation_name).observe(duration)
                logger.info('Время выполнения %s: %.6f секунд', operation_name, duration)

        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.perf_counter()
                duration = end_time - start_time
                LATENCY.labels(operation=operation_name).observe(duration)
                logger.info('Время выполнения %s: %.6f секунд', operation_name, duration)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator
