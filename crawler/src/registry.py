from typing import ClassVar

from crawler.base import BaseCrawler
from crawler.snuco import SnucoCrawler
from crawler.snudorm import SnudormCrawler
from crawler.snuvet import SnuvetCrawler


class CrawlerRegistry:
    """Registry for crawler classes."""

    _crawlers: ClassVar[dict[str, type[BaseCrawler]]] = {
        "snuco": SnucoCrawler,
        "snudorm": SnudormCrawler,
        "snuvet": SnuvetCrawler,
    }

    @classmethod
    def get_crawler(cls, source: str) -> type[BaseCrawler]:
        """Get crawler class for a source."""
        if source not in cls._crawlers:
            raise ValueError(f"No crawler registered for source: {source}")
        return cls._crawlers[source]

    @classmethod
    def get_all_crawlers(cls) -> list[type[BaseCrawler]]:
        """Get all registered crawler classes."""
        return list(cls._crawlers.values())
