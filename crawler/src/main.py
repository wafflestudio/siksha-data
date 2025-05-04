import argparse
from datetime import datetime, timedelta

from categorizer import MenuCategorizer
from crawler.base import BaseCrawler
from models import BreakfastSchedule, DinnerSchedule, LunchSchedule
from normalizer import MenuNormalizer
from registry import CrawlerRegistry


def parse_args():
    parser = argparse.ArgumentParser(description="Run all registered crawlers")
    parser.add_argument(
        "--days", type=int, default=7, help="Number of days to crawl in future (default: 7)"
    )
    return parser.parse_args()


def run_crawlers(days: int) -> list[BreakfastSchedule | LunchSchedule | DinnerSchedule]:
    crawlers: list[type[BaseCrawler]] = CrawlerRegistry.get_all_crawlers()
    start_date = datetime.today()

    schedules = []

    for crawler_class in crawlers:
        if crawler_class.supports_date:
            for i in range(days):
                target_date = start_date + timedelta(days=i)
                print(f"Running crawler: {crawler_class.__name__} for {target_date}")
                crawler = crawler_class()
                try:
                    schedules.extend(crawler.crawl(target_date))
                except Exception as e:
                    print(f"Error running {crawler_class.__name__}: {e!s}")
        else:
            print(f"Running crawler: {crawler_class.__name__} at {datetime.today()}")
            crawler = crawler_class()
            try:
                schedules.extend(crawler.crawl())
            except Exception as e:
                print(f"Error running {crawler_class.__name__}: {e!s}")

    return schedules


def normalize_menus(schedules: list[BreakfastSchedule | LunchSchedule | DinnerSchedule]):
    normalizer = MenuNormalizer()

    for schedule in schedules:
        schedule.menu.canonical_name = normalizer.normalize(schedule.menu.name)


def categorize_menus(schedules: list[BreakfastSchedule | LunchSchedule | DinnerSchedule]):
    categorizer = MenuCategorizer()

    for schedule in schedules:
        schedule.menu.category = categorizer.categorize(schedule.menu.canonical_name)


def main():
    args = parse_args()
    schedules = run_crawlers(args.days)
    normalize_menus(schedules)
    categorize_menus(schedules)


if __name__ == "__main__":
    main()
