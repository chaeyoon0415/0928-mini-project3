# 필요한 라이브러리를 불러온다
import pandas as pd

# 이 스크립트 파일 위치를 기준으로 clean.csv 경로를 정의한다
from pathlib import Path

INPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "clean.csv"

# clean.csv를 읽기만 한다 (원본은 수정하지 않는다)
df = pd.read_csv(INPUT_PATH, encoding="utf-8-sig")

# price 열의 개수를 센다
price_count = df["price"].count()

# price 열의 최소값을 구한다
price_min = df["price"].min()

# price 열의 최대값을 구한다
price_max = df["price"].max()

# price 열의 평균을 소수 둘째 자리까지 반올림한다
price_mean = round(df["price"].mean(), 2)

# price 열의 중앙값을 계산된 그대로 구한다
price_median = df["price"].median()

# 최소값을 가진 행을 찾는다 (같은 최소값이 여럿이면 첫 번째 행)
min_row = df[df["price"] == price_min].iloc[0]

# 최대값을 가진 행을 찾는다 (같은 최대값이 여럿이면 첫 번째 행)
max_row = df[df["price"] == price_max].iloc[0]

# clean.csv 전체 행 수를 구한다
total_rows = len(df)

# price 개수와 전체 행 수가 같은지 비교한다
count_matches = "같음" if price_count == total_rows else "다름"

# 마크다운 표 형식으로 결과를 출력한다
print("| 항목 | 값 |")
print("|---|---|")
print(f"| 개수 | {price_count} |")
print(f"| 최소 | {price_min} (name: {min_row['name']}, rating: {min_row['rating']}) |")
print(f"| 최대 | {price_max} (name: {max_row['name']}, rating: {max_row['rating']}) |")
print(f"| 평균 | {price_mean} |")
print(f"| 중앙값 | {price_median} |")
print()

# 개수와 전체 행 수를 나란히 출력하고 같음/다름을 밝힌다
print(f"price 개수: {price_count}  clean.csv 전체 행 수: {total_rows}  -> {count_matches}")
