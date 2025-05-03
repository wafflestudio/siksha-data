from typing import ClassVar


class MenuCategorizer:
    CATEGORY_MAP: ClassVar[dict[str, list[str]]] = {
        "한식-찌개/국밥": ["국밥", "찌개", "전골", "청국장", "순두부"],
        "한식-비빔밥/덮밥": ["비빔밥", "덮밥", "제육", "수육", "불고기"],
        "한식-구이/볶음": ["구이", "볶음", "강정"],
        "한식-면류": ["국수", "냉면", "칼국수"],
        "양식-파스타/그라탕": ["파스타", "그라탕", "라자냐"],
        "양식-스테이크/패스트푸드": ["스테이크", "햄버거", "핫도그", "피자"],
        "중식-면류": ["짜장", "짬뽕", "우육면"],
        "중식-밥류": ["볶음밥", "마파두부"],
        "중식-튀김/요리": ["탕수육", "깐풍기", "양장피", "딤섬"],
        "일식-초밥/회": ["초밥", "사시미", "회덮밥"],
        "일식-덮밥": ["가츠동", "사케동", "덮밥"],
        "일식-면류": ["우동", "라멘", "소바"],
        "기타-퓨전": ["퓨전", "이색", "토스트", "브런치"],
        "기타-간식/분식": ["떡볶이", "김밥", "만두", "분식"],
        "기타-채식/건강식": ["채식", "건강식", "샐러드", "곤약"],
    }

    @classmethod
    def categorize(cls, menu_name: str) -> str:
        """Category the menu name to a category."""
        for category, keywords in cls.CATEGORY_MAP.items():
            if any(keyword in menu_name for keyword in keywords):
                return category
        return "분류없음"

    @classmethod
    def get_category_map(cls) -> dict[str, list[str]]:
        """Return the category map."""
        return cls.CATEGORY_MAP.copy()
