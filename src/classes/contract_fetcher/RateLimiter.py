import logging
import time

from rich.console import Console

# Initialize rich console for better logging
console = Console()
logging.basicConfig(level=logging.INFO)


class RateLimiter:
    """
    A class to enforce rate limiting for API requests or any actions that need to be limited over time.
    """

    def __init__(self, limit: int) -> None:
        """
        Initializes the RateLimiter with the specified limit for requests per second.

        :param limit: The number of requests allowed per second.
        :type limit: int
        """
        self.limit = limit
        self.request_count = 0
        self.last_request_time = time.time()

    def rate_limit(self) -> None:
        """
        Enforces rate limiting by checking the current request count and time.
        Pauses execution if the request limit has been reached to ensure compliance with the rate limit.
        """
        current_time = time.time()
        if self.request_count >= self.limit and (current_time - self.last_request_time) < 1:
            time_to_wait = 1 - (current_time - self.last_request_time)
            console.log(f"[yellow]Rate limit reached. Sleeping for {time_to_wait:.2f} seconds...[/yellow]")
            time.sleep(time_to_wait)
            self.request_count = 0
        elif (current_time - self.last_request_time) >= 1:
            self.request_count = 0
            self.last_request_time = time.time()

    def increment_request_count(self) -> None:
        """
        Increments the request count by 1.
        This should be called after every request or action that is subject to rate limiting.
        """
        self.request_count += 1
