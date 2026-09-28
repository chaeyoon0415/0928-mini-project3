# 필요한 라이브러리를 불러온다
from pathlib import Path

import matplotlib

# 화면 표시 없이 파일로만 저장하기 위해 비대화형 백엔드를 사용한다
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

# 이 스크립트 파일 위치를 기준으로 입력/출력 경로를 정의한다
INPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "clean.csv"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "charts" / "by_category.png"

# clean.csv를 읽기만 한다 (원본은 수정하지 않는다)
df = pd.read_csv(INPUT_PATH, encoding="utf-8-sig")

# clean.csv 전체 행 수를 구한다 (마지막 비교에 사용)
total_rows = len(df)

# 전체 데이터에 실제로 존재하는 rating 값을 오름차순으로 모은다 (두 그래프의 가로축 범주로 함께 쓴다)
all_categories = sorted(df["rating"].dropna().unique().tolist())

# price_unit별 막대 색을 고정 순서로 지정한다 (회=blue, 월=orange, 데이터비즈 팔레트 slot 1/2)
color_by_unit = {"회": "#2a78d6", "월": "#eb6834"}

# 그림 안에서 쓸 영어 라벨을 매핑한다 (그림 안 글자는 모두 영어로)
unit_label_en = {"회": "per-visit", "월": "per-month"}

# 두 단위를 나란히 그리기 위해 서브플롯 2개를 만든다
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# 각 단위별 결과를 저장해 둘 딕셔너리 (마크다운 표 출력에 사용)
results_by_unit = {}

for ax, unit in zip(axes, ["회", "월"]):
    # 이 단위에 해당하는 행만 뽑는다
    sub = df[df["price_unit"] == unit]

    # rating별로 개수/합/평균을 계산한다 (서로 다른 단위를 섞지 않도록 unit별로 따로 계산)
    grouped = sub.groupby("rating")["price"].agg(count="count", sum="sum", mean="mean")

    # 이 단위의 결과를 나중에 표로 출력하기 위해 저장한다
    results_by_unit[unit] = {"grouped": grouped, "unit_rows": len(sub)}

    # 막대를 그릴 x좌표(범주 위치)를 준비한다
    x_positions = range(len(all_categories))

    for x, rating in zip(x_positions, all_categories):
        if rating in grouped.index:
            # 자료가 있는 범주만 막대를 그린다
            mean_price = grouped.loc[rating, "mean"]
            n = int(grouped.loc[rating, "count"])

            ax.bar(x, mean_price, color=color_by_unit[unit], width=0.6)

            # 막대 위에 평균(소수 둘째 자리)과 n을 두 줄로 적는다 (그림 안 글자는 영어로)
            ax.text(
                x,
                mean_price,
                f"{mean_price:.2f}\nn={n}",
                ha="center",
                va="bottom",
                fontsize=8,
            )
        else:
            # 자료가 없는 범주는 막대를 그리지 않고, 그림에는 영어로 N/A만 표시한다
            ax.text(x, 0, "N/A", ha="center", va="bottom", fontsize=8)

    # 가로축을 rating 값(오름차순)으로 지정한다
    ax.set_xticks(list(x_positions))
    ax.set_xticklabels([str(r) for r in all_categories])

    # 가로축 제목을 붙인다
    ax.set_xlabel("Rating (stars)")

    # 세로축 제목을 붙인다
    ax.set_ylabel("Average price (KRW)")

    # 제목에 price_unit과 이 그룹의 전체 n을 적는다 (그림 안 글자는 영어로)
    ax.set_title(f"price_unit = {unit_label_en[unit]} (n = {len(sub)})")

# 그래프끼리 겹치지 않도록 여백을 정리한다
fig.tight_layout()

# charts 폴더가 없으면 만들어 둔다
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# 그래프를 파일로 저장한다 (화면 표시는 하지 않는다)
fig.savefig(OUTPUT_PATH)

print("저장 완료:", OUTPUT_PATH)
print()

# 단위별로 범주별 개수/합/평균 표를 출력한다
for unit in ["회", "월"]:
    grouped = results_by_unit[unit]["grouped"]
    unit_rows = results_by_unit[unit]["unit_rows"]

    print(f"=== price_unit = {unit} ===")
    print("| 범주 | 개수 | 합 | 평균 |")
    print("|---|---|---|---|")

    count_sum = 0
    for rating in all_categories:
        if rating in grouped.index:
            count = int(grouped.loc[rating, "count"])
            price_sum = grouped.loc[rating, "sum"]
            mean_price = grouped.loc[rating, "mean"]
            print(f"| {rating} | {count} | {price_sum:.0f} | {mean_price:.2f} |")
            count_sum += count
        else:
            # 값이 없는 범주는 "자료 없음"으로 적는다
            print(f"| {rating} | 자료 없음 | 자료 없음 | 자료 없음 |")

    # 개수 합과 이 price_unit의 전체 행 수를 나란히 적는다
    match_result = "같음" if count_sum == unit_rows else "다름"
    print(f"개수 합: {count_sum}  price_unit={unit} 전체 행 수: {unit_rows}  -> {match_result}")
    print()

# 회와 월의 개수 합이 clean.csv 전체 행 수와 같은지 적는다
combined_rows = results_by_unit["회"]["unit_rows"] + results_by_unit["월"]["unit_rows"]
combined_match = "같음" if combined_rows == total_rows else "다름"
print(f"회+월 행 수 합: {combined_rows}  clean.csv 전체 행 수: {total_rows}  -> {combined_match}")
