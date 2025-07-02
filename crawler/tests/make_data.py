import csv
import glob
import operator
import os
from datetime import datetime, timedelta

from src.categorizer import MenuCategorizer
from src.normalizer import MenuNormalizer
from src.registry import CrawlerRegistry


class DataMaker:
    @classmethod
    def get_html_files(cls, raw_html_dir: str, source: str) -> list[tuple[str, datetime]]:
        """Get all HTML files for a specific source with their dates.

        Args:
            raw_html_dir: Directory containing raw HTML files
            source: Source name to match files for

        Returns:
            List of tuples containing (filename, date) for each matching file
        """
        pattern = os.path.join(raw_html_dir, f"{source}_*.html")
        files = glob.glob(pattern)

        if not files:
            raise FileNotFoundError(f"No HTML files found for source: {source}")

        test_files = []
        for file_path in sorted(files):
            file_name = os.path.basename(file_path)
            date_parts = file_name.replace(".html", "").split("_")[1:]  # [YYYY, MM, DD]
            test_date = datetime(
                int(date_parts[0]),  # YYYY
                int(date_parts[1]),  # MM
                int(date_parts[2]),  # DD
            )
            test_files.append((file_name, test_date))

        return test_files

    @classmethod
    def generate_raw_html(
        cls, output_dir: str, days: int = 7, go_past: bool = True, sources: list[str] | None = None
    ):
        """Generate raw HTML files for specified number of days.

        Args:
            output_dir: Directory to save raw HTML files
            days: Number of days to generate data for
            go_past: If True, go past days. If False, go future days. (default: True)
            sources: List of sources to generate data for. If None, uses all registered crawlers.

        """
        print(f"Generating raw HTML files for {days} days")

        crawl_date = datetime.now()  # 크롤링 실행 날짜
        op = operator.sub if go_past else operator.add

        if sources is None:
            sources = list(CrawlerRegistry._crawlers.keys())

        os.makedirs(output_dir, exist_ok=True)

        for source in sources:
            try:
                crawler_class = CrawlerRegistry.get_crawler(source)
                crawler = crawler_class()

                if crawler.supports_date:
                    for i in range(days):
                        target_date = op(crawl_date, timedelta(days=i))
                        filename = f"{source}_{target_date.strftime('%Y_%m_%d')}.html"
                        filepath = os.path.join(output_dir, filename)
                        try:
                            html = crawler.fetch_html(target_date)
                            with open(filepath, "w", encoding="utf-8") as f:
                                f.write(html)
                            print(f"Created: {filename}")
                        except Exception as e:
                            print(f"Error ({filename}): {e!s}")
                else:
                    filename = f"{source}_{crawl_date.strftime('%Y_%m_%d')}.html"
                    filepath = os.path.join(output_dir, filename)
                    try:
                        html = crawler.fetch_html(crawl_date)
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(html)
                        print(f"Created: {filename}")
                    except Exception as e:
                        print(f"Error ({filename}): {e!s}")

            except ValueError as e:
                print(f"Error getting crawler for {source}: {e!s}")

    @classmethod
    def generate_training_data(
        cls,
        raw_html_dir: str,
        output_dir: str,
        days: int = 7,
        go_past: bool = True,
        sources: list[str] | None = None,
    ):
        """Generate training data for normalizer and categorizer from raw HTML files and save to CSV.

        Args:
            raw_html_dir: Directory containing raw HTML files
            output_dir: Directory to save training data files
            days: Number of days to generate data for
            go_past: If True, go past days. If False, go future days. (default: True)
            sources: List of sources to generate data for. If None, uses all registered crawlers.
        """
        if sources is None:
            sources = list(CrawlerRegistry._crawlers.keys())

        os.makedirs(output_dir, exist_ok=True)
        normalizer = MenuNormalizer()
        categorizer = MenuCategorizer()
        all_data = []

        for source in sources:
            try:
                crawler_class = CrawlerRegistry.get_crawler(source)
                crawler = crawler_class()

                # Get all HTML files for this source
                html_files = cls.get_html_files(raw_html_dir, source)

                for html_file, date in html_files:
                    diff = datetime.now().date() - date.date()
                    if (
                        abs(diff.days) > days
                        or (go_past and diff.days < 0)
                        or (not go_past and diff.days > 0)
                    ):
                        continue

                    filepath = os.path.join(raw_html_dir, html_file)
                    with open(filepath, encoding="utf-8") as f:
                        html_content = f.read()

                    # Parse HTML and get schedules
                    schedules = crawler.parse(html_content, date)

                    # Extract menu names and their normalized versions
                    for schedule in schedules:
                        menu_name = schedule.menu.name
                        canonical_name = normalizer.normalize(menu_name)
                        category = (
                            categorizer.categorize(canonical_name) if canonical_name else None
                        )
                        all_data.append(
                            {
                                "date": date,
                                "source": source,
                                "menu_name": menu_name,
                                "canonical_name": canonical_name,
                                "category": category.value if category else "분류없음",
                            }
                        )

                print(f"Generated training data for {source}: {len(all_data)} entries")

            except Exception as e:
                print(f"Error generating training data for {source}: {e!s}")

        # Save all training data to a single CSV file with current date
        current_date = datetime.now().strftime("%Y%m%d")
        csv_filepath = os.path.join(output_dir, f"training_data_{current_date}.csv")
        with open(csv_filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=["date", "source", "menu_name", "canonical_name", "category"]
            )
            writer.writeheader()
            writer.writerows(all_data)
        print(f"Saved all training data to {csv_filepath}: {len(all_data)} total entries")
