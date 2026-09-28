# 필요한 라이브러리를 불러온다
import re
from pathlib import Path

import pandas as pd

# 이 스크립트 파일 위치를 기준으로 입력/출력 경로를 정의한다
INPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "raw.csv"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "clean.csv"

# raw.csv를 읽기만 한다 (원본은 수정하지 않는다)
df = pd.read_csv(INPUT_PATH, encoding="utf-8-sig")


def report(title, frame):
    # 처리 전/후 상태를 같은 형식으로 출력하기 위한 함수
    print(f"=== {title} ===")
    print("행 수:", len(frame))
    print("데이터형:")
    print(frame.dtypes)
    print("열별 빈칸 수:")
    print(frame.isna().sum())
    print(
        "detail_url 중복 수:",
        len(frame) - frame["detail_url"].nunique() if "detail_url" in frame.columns else "-",
    )
    print()


# 정제 전 상태를 출력한다
report("정제 전 (raw.csv)", df)


# 1) price_raw에서 쉼표와 "원~"을 제거하고 숫자만 뽑아 price 열을 만든다
def extract_price(value):
    if pd.isna(value):
        return pd.NA
    digits = re.sub(r"[^0-9]", "", str(value))
    if digits == "":
        return pd.NA
    return int(digits)


df.insert(df.columns.get_loc("price_raw") + 1, "price", df["price_raw"].apply(extract_price))
df["price"] = df["price"].astype("Int64")


# 2) price_raw에서 "/회", "/월"을 구분해 price_unit 열을 만든다
def extract_unit(value):
    if pd.isna(value):
        return pd.NA
    text = str(value)
    if "/회" in text:
        return "회"
    if "/월" in text:
        return "월"
    return pd.NA


df.insert(df.columns.get_loc("price") + 1, "price_unit", df["price_raw"].apply(extract_unit))


# 3) rating_raw에서 괄호 앞의 평점 숫자만 뽑아 rating 열을 만든다 (예: 5.0(5) -> 5.0)
def extract_rating(value):
    if pd.isna(value):
        return pd.NA
    match = re.match(r"\s*([0-9]+(?:\.[0-9]+)?)\s*\(", str(value))
    if not match:
        return pd.NA
    return float(match.group(1))


df.insert(df.columns.get_loc("rating_raw") + 1, "rating", df["rating_raw"].apply(extract_rating))
df["rating"] = pd.to_numeric(df["rating"], errors="coerce")


# 4) location_raw의 앞뒤 공백과 연속 공백을 정리해 location 열을 만든다
def clean_location(value):
    if pd.isna(value):
        return pd.NA
    return re.sub(r"\s+", " ", str(value)).strip()


df.insert(df.columns.get_loc("location_raw") + 1, "location", df["location_raw"].apply(clean_location))


# 숫자로 바꾸지 못한 원문 값(있다면)을 출력한다
price_failed = df[df["price_raw"].notna() & df["price"].isna()]
if len(price_failed) > 0:
    print("=== price로 변환하지 못한 원문 값 ===")
    for idx, row in price_failed.iterrows():
        print(f"행 {idx}: price_raw={row['price_raw']!r} -> NaN 유지")
else:
    print("price로 변환하지 못한 값 없음")

rating_failed = df[df["rating_raw"].notna() & df["rating"].isna()]
if len(rating_failed) > 0:
    print("=== rating으로 변환하지 못한 원문 값 ===")
    for idx, row in rating_failed.iterrows():
        print(f"행 {idx}: rating_raw={row['rating_raw']!r} -> NaN 유지")
else:
    print("rating으로 변환하지 못한 값 없음")
print()


# 6) name, price, rating, detail_url 중 빈칸인 행을 사유와 함께 먼저 출력한 뒤 제외한다
required_cols = ["name", "price", "rating", "detail_url"]
blank_mask = df[required_cols].isna().any(axis=1)
blank_rows = df[blank_mask]

print("=== 필수값(name/price/rating/detail_url) 빈칸으로 제외되는 행 ===")
if len(blank_rows) == 0:
    print("해당 없음")
else:
    for idx, row in blank_rows.iterrows():
        missing = [c for c in required_cols if pd.isna(row[c])]
        print(f"행 {idx}: name={row['name']!r}  빈 열={missing}")
print()

df = df[~blank_mask]


# 7) detail_url이 중복된 경우 처음 한 행만 남기고 제외한 행과 사유를 출력한다
dup_mask = df.duplicated(subset="detail_url", keep="first")
dup_rows = df[dup_mask]

print("=== detail_url 중복으로 제외되는 행 (처음 1행만 유지) ===")
if len(dup_rows) == 0:
    print("해당 없음")
else:
    for idx, row in dup_rows.iterrows():
        print(f"행 {idx}: name={row['name']!r}  detail_url={row['detail_url']!r} -> 중복이라 제외")
print()

df = df[~dup_mask]

# 정제 후 상태를 출력한다 (인덱스는 정리하지 않고 원래 행 번호를 그대로 유지)
report("정제 후 (제외 처리 반영)", df)

# data 폴더가 없으면 만들어 둔다
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# 정제 결과를 CSV로 저장한다 (한글 깨짐 방지용 utf-8-sig)
df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

print("저장 완료:", OUTPUT_PATH)
