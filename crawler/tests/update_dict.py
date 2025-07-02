from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from collections.abc import Iterable
from datetime import datetime

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────
ALLOWED_CATEGORIES: list[str] = [
    # 한식
    "한식>찌개/국밥",
    "한식>비빔밥/덮밥",
    "한식>구이/볶음",
    "한식>면류",
    "한식>조림",
    # 양식
    "양식>파스타/그라탕",
    "양식>스테이크/패스트푸드",
    # 중식
    "중식>면류",
    "중식>밥류",
    "중식>튀김/요리",
    # 일식
    "일식>초밥/회",
    "일식>덮밥",
    "일식>면류",
    # 기타
    "기타>퓨전",
    "기타>간식/분식",
    "기타>채식/건강식",
    "기타",
]

# 기본 경로 설정
DEFAULT_TRAIN_DIR = pathlib.Path(__file__).parent / "back_test_data" / "training_data"
DEFAULT_DICT_PATH = pathlib.Path(__file__).parent.parent / "src" / "resources" / "menu_dict.jsonl"
RESOURCES_DIR = pathlib.Path(__file__).parent.parent / "src" / "resources"


def find_csv_files(directory: pathlib.Path) -> list[pathlib.Path]:
    """Find all CSV files in the given directory."""
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    return sorted(directory.glob("*.csv"))


def load_training_data(path: pathlib.Path) -> pd.DataFrame:
    return pd.read_csv(path)


def load_menu_dict(path: pathlib.Path) -> tuple[list[dict], dict[str, dict], set[str]]:
    """메뉴 사전을 로드하고 중복 체크를 위한 인덱스를 생성합니다."""
    items: list[dict] = []
    canonical_to_item: dict[str, dict] = {}
    menu_names: set[str] = set()

    if not path.exists():
        path.touch()
        return items, canonical_to_item, menu_names

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                items.append(item)
                canonical_to_item[item["canonical_name"]] = item
                menu_names.add(item["menu_name"])

    return items, canonical_to_item, menu_names


def dump_menu_dict(path: pathlib.Path, items: Iterable[dict]):
    """메뉴 사전을 파일에 저장합니다."""
    items_sorted = sorted(items, key=lambda x: x["canonical_name"])
    with path.open("w", encoding="utf-8") as f:
        for item in items_sorted:
            json.dump(item, f, ensure_ascii=False)
            f.write("\n")
    print(f"  → 총 {len(items_sorted)}개의 항목이 저장되었습니다.")


def prompt_with_default(question: str, default: str) -> str:
    """Return user input or default."""
    resp = input(f"{question} [{default}]: ")
    if resp.lower() in {"q", "quit", "exit"}:
        if input("현재 작업을 저장하시겠습니까? (ㅇ/ㄴ): ").lower() == "ㅇ":
            return "save_and_quit"
        sys.exit(0)
    return default if resp == "" else resp


def select_category(default_category: str) -> str:
    """카테고리를 숫자로 선택하도록 합니다."""
    print("\n허용 카테고리:")
    for i, category in enumerate(ALLOWED_CATEGORIES, 1):
        print(f"  {i}. {category}")

    while True:
        try:
            choice = input(
                f"→ 카테고리 번호 선택 (1-{len(ALLOWED_CATEGORIES)}) [{ALLOWED_CATEGORIES.index(default_category) + 1}]: "
            ).strip()
            if choice.lower() in {"q", "quit", "exit"}:
                if input("현재 작업을 저장하시겠습니까? (ㅇ/ㄴ): ").lower() == "ㅇ":
                    return "save_and_quit"
                sys.exit(0)

            if not choice:
                return default_category

            idx = int(choice) - 1
            if 0 <= idx < len(ALLOWED_CATEGORIES):
                return ALLOWED_CATEGORIES[idx]

            print(f"⚠️ 1부터 {len(ALLOWED_CATEGORIES)} 사이의 숫자를 입력하세요.")
        except ValueError:
            print("⚠️ 숫자를 입력하세요.")


def save_with_options(items: Iterable[dict], default_path: pathlib.Path):
    """파일 저장 옵션을 제공합니다."""
    while True:
        print("\n파일 저장 옵션:")
        print("1. 기존 파일 덮어쓰기")
        print("2. 새 파일로 저장 (타임스탬프 추가)")

        choice = input("→ 선택 (1-2): ").strip()

        if choice == "1":
            if default_path.exists():
                if input(f"'{default_path}'를 덮어쓰시겠습니까? (ㅇ/ㄴ): ").lower() != "ㅇ":
                    continue
            dump_menu_dict(default_path, items)
            print(f"\n✅ 파일이 저장되었습니다: {default_path}")
            return default_path

        elif choice == "2":
            timestamp = datetime.now().strftime("%Y%m%d-%H%M")
            new_path = default_path.with_name(
                f"{default_path.stem}_{timestamp}{default_path.suffix}"
            )
            dump_menu_dict(new_path, items)
            print(f"\n✅ 새 파일이 저장되었습니다: {new_path}")
            return new_path

        else:
            print("⚠️ 1, 2 중 하나를 선택하세요.")


def train_model(dict_path: pathlib.Path):
    """메뉴 분류 모델을 재학습합니다."""
    print("\n모델 재학습을 시작합니다...")

    # 데이터 로드
    train_df = pd.read_json(dict_path, orient="records", lines=True)
    x = train_df["canonical_name"]
    y = train_df["category"]

    # 모델 학습
    pipe = make_pipeline(
        TfidfVectorizer(analyzer="char", ngram_range=(2, 4), min_df=3),
        LogisticRegression(max_iter=200, C=10, class_weight="balanced", random_state=42),
    )
    pipe.fit(x, y)

    # 모델 저장
    timestamp = datetime.now().strftime("%Y%m%d")
    model_path = RESOURCES_DIR / f"menu_classifier_{timestamp}.joblib"
    joblib.dump(pipe, model_path, compress=3)

    print(f"✅ 모델이 저장되었습니다: {model_path}")


def clear_screen():
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def run_reviewer(train_dir: pathlib.Path, dict_path: pathlib.Path):
    csv_files = find_csv_files(train_dir)
    if not csv_files:
        print(f"❌ No CSV files found in {train_dir}")
        sys.exit(1)

    print(f"\n📂 Found {len(csv_files)} CSV files:")
    for i, f in enumerate(csv_files, 1):
        print(f"  {i}. {f.name}")

    df = pd.concat([load_training_data(f) for f in csv_files], ignore_index=True)
    items, canonical_to_item, menu_names = load_menu_dict(dict_path)

    print("\n────────────────────────────────────────────────────────────────────────────")
    print(f"🗂️ Training files: {len(csv_files)} files in {train_dir}")
    print(f"📓 Dictionary    : {dict_path} ({len(items)} records loaded)")
    print("────────────────────────────────────────────────────────────────────────────\n")

    for idx, row in df.iterrows():
        clear_screen()
        original_name = row.get("menu_name")
        canonical_name = row.get("canonical_name", original_name)
        category = row.get("category", "기타")

        print("=" * 80)
        print(f"[{idx + 1}/{len(df)}] 원본: {original_name}")

        # 메뉴 이름 중복 체크
        if original_name in menu_names:
            existing_item = next(
                (item for item in items if item["menu_name"] == original_name), None
            )
            if existing_item:
                print(f"\n⚠️ 경고: '{original_name}'는 이미 사전에 존재합니다.")
                print(f"  - 정규화된 이름: {existing_item['canonical_name']}")
                print(f"  - 카테고리: {existing_item['category']}")
                if input("  이 항목을 덮어쓰시겠습니까? (ㅇ/ㄴ): ").lower() != "ㅇ":
                    continue
                # 기존 항목 제거
                items.remove(existing_item)
                menu_names.remove(original_name)
                if existing_item["canonical_name"] in canonical_to_item:
                    del canonical_to_item[existing_item["canonical_name"]]

        new_canonical_name = prompt_with_default("→ 정규화된 이름", canonical_name)
        if new_canonical_name == "save_and_quit":
            break
        elif new_canonical_name == canonical_name:
            print(f"  → 정규화된 이름을 변경하지 않습니다: {new_canonical_name}")
        elif new_canonical_name == " ":  # Space 입력 시 원본 이름 사용
            new_canonical_name = original_name
            print(f"  → 원본 이름을 사용합니다: {new_canonical_name}")

        category = select_category(category)
        if category == "save_and_quit":
            break

        new_item = {
            "menu_name": original_name,
            "canonical_name": new_canonical_name,
            "category": category,
        }
        items.append(new_item)
        canonical_to_item[new_canonical_name] = new_item
        menu_names.add(original_name)

    saved_path = save_with_options(items, dict_path)
    print("\n✅ 검수가 완료되었습니다: 사전이 업데이트되었습니다 (정렬: canonical_name).")

    if input("\n모델을 재학습하시겠습니까? (ㅇ/ㄴ): ").lower() == "ㅇ":
        train_model(saved_path)

    return items


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Menu labeling tool")
    ap.add_argument(
        "-t",
        "--train",
        metavar="DIR",
        default=str(DEFAULT_TRAIN_DIR),
        help=f"Directory containing training_data CSV files (default: {DEFAULT_TRAIN_DIR})",
    )
    ap.add_argument(
        "-d",
        "--dict",
        metavar="JSONL",
        default=str(DEFAULT_DICT_PATH),
        help=f"Path to menu_dict.jsonl (default: {DEFAULT_DICT_PATH})",
    )
    return ap.parse_args()


def main():
    args = parse_args()
    train_dir = pathlib.Path(args.train)
    dict_path = pathlib.Path(args.dict)

    try:
        items = run_reviewer(train_dir, dict_path)
    except KeyboardInterrupt:
        print("\n⏹️ 검수가 중단되었습니다.")
        if input("현재 작업을 저장하시겠습니까? (ㅇ/ㄴ): ").lower() == "ㅇ":
            # 현재까지 처리된 항목들을 저장
            saved_path = save_with_options(items, dict_path)
            print(f"✅ 작업이 저장되었습니다: {saved_path}")

        if input("\n모델을 재학습하시겠습니까? (ㅇ/ㄴ): ").lower() == "ㅇ":
            train_model(saved_path)
        sys.exit(1)


if __name__ == "__main__":
    main()
