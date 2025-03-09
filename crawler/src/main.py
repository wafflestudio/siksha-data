import argparse
from datetime import datetime, timedelta

from crawler.base import BaseCrawler
from crawler.registry import CrawlerRegistry


def parse_args():
    parser = argparse.ArgumentParser(description="Run all registered crawlers")
    parser.add_argument("--days", type=int, default=7, help="Number of days to crawl (default: 7)")
    return parser.parse_args()


def run_crawlers(days: int):
    start_date = datetime.now() - timedelta(days=days)
    crawlers: list[type[BaseCrawler]] = CrawlerRegistry.get_all_crawlers()

    for crawler_class in crawlers:
        print(f"Running crawler: {crawler_class.__name__}")
        crawler = crawler_class()
        try:
            schedules = crawler.crawl(start_date)
            for schedule in schedules:
                print(f"{schedule.cafeteria.name}: {schedule.menu}")
        except Exception as e:
            print(f"Error running {crawler_class.__name__}: {e!s}")


def main():
    args = parse_args()
    run_crawlers(args.days)


if __name__ == "__main__":
    main()
