from abc import ABC, abstractmethod
from datetime import datetime

from models import BreakfastSchedule, DinnerSchedule, LunchSchedule


class BaseCrawler(ABC):
    """Base class for all crawlers that defines the common interface."""

    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base URL for the crawler."""
        pass

    @property
    @abstractmethod
    def supports_date(self) -> bool:
        """Whether this crawler supports date parameter."""
        pass

    @abstractmethod
    def fetch_html(self, date: datetime | None = None) -> str:
        """Fetch HTML content from the source.

        Args:
            date: Optional date to fetch data for. If None, fetches current data.
                 Some crawlers may not support this parameter.

        Returns:
            HTML content as string

        """
        pass

    @abstractmethod
    def parse(
        self, html_content: str, date: datetime
    ) -> list[BreakfastSchedule | LunchSchedule | DinnerSchedule]:
        """Parse HTML content and return structured data.

        Args:
            html_content: HTML content to parse
            date: Date the content is for

        Returns:
            List of Schedule objects (BreakfastSchedule, LunchSchedule, or DinnerSchedule)

        """
        pass

    def crawl(
        self, date: datetime | None = None
    ) -> list[BreakfastSchedule | LunchSchedule | DinnerSchedule]:
        """Crawl and parse data from the source.

        Args:
            date: Optional date to crawl data for. If None, crawls current data.
                 Some crawlers may not support this parameter.

        Returns:
            List of Schedule objects (BreakfastSchedule, LunchSchedule, or DinnerSchedule)

        """
        html_content = self.fetch_html(date)
        return self.parse(html_content, date)
