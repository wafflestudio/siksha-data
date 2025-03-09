import os
from datetime import datetime, timedelta
from typing import Optional

from src.registry import CrawlerRegistry


class DataMaker:
    def __init__(self, output_dir: str = "tests/back_test_data/raw_html"):
        self.output_dir = output_dir

    def save_html(self, html: str, filename: str):
        """Save HTML to file."""
        os.makedirs(self.output_dir, exist_ok=True)
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

    def generate_test_data(self, days: int = 7, sources: Optional[list[str]] = None):
        """Generate test data for specified number of days.

        Args:
            days: Number of days to generate data for
            sources: List of sources to generate data for. If None, uses all registered crawlers.

        """
        print(f"Generating test data for {days} days")

        crawl_date = datetime.now()  # 크롤링 실행 날짜

        if sources is None:
            sources = list(CrawlerRegistry._crawlers.keys())

        for source in sources:
            try:
                crawler_class = CrawlerRegistry.get_crawler(source)
                crawler = crawler_class()

                if crawler.supports_date:
                    for i in range(days):
                        target_date = crawl_date + timedelta(days=i)
                        filename = f"{source}_{target_date.strftime('%Y_%m_%d')}.html"
                        try:
                            html = crawler.fetch_html(target_date)
                            self.save_html(html, filename)
                            print(f"Created: {filename}")
                        except Exception as e:
                            print(f"Error ({filename}): {e!s}")
                else:
                    filename = f"{source}_{crawl_date.strftime('%Y_%m_%d')}.html"
                    try:
                        html = crawler.fetch_html(crawl_date)
                        self.save_html(html, filename)
                        print(f"Created: {filename}")
                    except Exception as e:
                        print(f"Error ({filename}): {e!s}")

            except ValueError as e:
                print(f"Error getting crawler for {source}: {e!s}")
