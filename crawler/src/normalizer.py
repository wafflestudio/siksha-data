import json
import re
from pathlib import Path

from rapidfuzz import fuzz, process


class MenuNormalizer:
    THRESHOLD = 80

    def __init__(self):
        mapping_path = Path(__file__).parent / "resources" / "menu_dict.jsonl"
        self.mapping_dict = {}
        for line in mapping_path.open("r", encoding="utf-8"):
            item = json.loads(line)
            self.mapping_dict[item["menu_name"]] = item["canonical_name"]

    def _rule_based_normalization(self, menu_name: str) -> str | None:
        """Normalize menu name using rule-based approach."""
        removed_parentheses = re.sub(r"\([^)]*\)", "", menu_name)
        removed_brackets = re.sub(r"\[.*?\]", "", removed_parentheses)
        return removed_brackets

    def _fuzzy_matching(self, menu_name: str) -> tuple[str, float]:
        """Normalize menu name using fuzzy matching."""
        best, score, _ = process.extractOne(menu_name, self.mapping_dict, scorer=fuzz.WRatio)
        return best, score

    def normalize(self, menu_name: str) -> str | None:
        """Normalize menu name using rapidfuzz."""
        rule_based_normalized_menu_name = self._rule_based_normalization(menu_name)
        best, score = self._fuzzy_matching(rule_based_normalized_menu_name)
        return best if score > self.THRESHOLD else None
