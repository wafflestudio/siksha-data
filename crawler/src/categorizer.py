from pathlib import Path
from sys import stderr

import joblib

from models import Category


class MenuCategorizer:
    MODEL_DATE = "20250504"

    def __init__(self):
        self.model = joblib.load(
            Path(__file__).parent / "resources" / f"menu_classifier_{self.MODEL_DATE}.joblib"
        )

    def categorize(self, menu_name: str) -> Category | None:
        """Category the menu name using pre-trained logistic regression model(tf-idf vectorizer)."""
        try:
            category_name = self.model.predict([menu_name])[0]
            return Category(category_name)
        except Exception as e:
            stderr.write(f"Error categorizing menu name: {e!s}\n")
            return None
