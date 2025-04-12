from typing import ClassVar

from crawler.base import BaseCrawler


class CrawlerRegistry:
    """Registry for crawler classes."""

    _crawlers: ClassVar[dict[str, type[BaseCrawler]]] = {}

    @classmethod
    def register(cls, source: str):
        """Register a crawler class for a source."""

        def decorator(crawler_class: type[BaseCrawler]):
            cls._crawlers[source] = crawler_class
            return crawler_class

        return decorator

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
