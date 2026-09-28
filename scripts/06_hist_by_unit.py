# 필요한 라이브러리를 불러온다
from pathlib import Path

import matplotlib

# 화면 표시 없이 파일로만 저장하기 위해 비대화형 백엔드를 사용한다
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 이 스크립트 파일 위치를 기준으로 입력/출력 경로를 정의한다
INPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "clean.csv"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "charts" / "hist_by_unit.png"

# clean.csv를 읽기만 한다 (원본은 수정하지 않는다)
df = pd.read_csv(INPUT_PATH, encoding="utf-8-sig")

# price_unit별로 구간 경계를 따로 둔다 ("회"와 "월"의 실제 가격 범위가 다르기 때문)
bin_edges_by_unit = {
    "회": [0, 10000, 20000, 30000, 40000, 50000, 60000, 70000],
    "월": [0, 20000, 40000, 60000, 80000, 100000, 120000, 140000],
}

# clean.csv 전체 행 수를 구한다 (같음/다름 비교에 사용)
total_rows = len(df)

# 두 단위를 나란히 그리기 위해 서브플롯 2개를 만든다
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# 각 단위별 결과를 저장해 둘 딕셔너리 (마크다운 표 출력에 사용)
results_by_unit = {}

for ax, unit in zip(axes, ["회", "월"]):
    # 이 단위에 해당하는 행만 뽑는다
    sub = df[df["price_unit"] == unit]

    # 이 단위에 맞는 구간 경계를 가져온다
    bin_edges = bin_edges_by_unit[unit]

    # numpy.histogram으로 구간별 개수를 센다
    # (왼쪽 끝 포함·오른쪽 끝 미포함이 기본이며, 마지막 구간만 양쪽 끝을 포함한다)
    counts, edges = np.histogram(sub["price"], bins=bin_edges)

    # 히스토그램 막대를 그린다
    n_out, bins_out, patches = ax.hist(sub["price"], bins=bin_edges, edgecolor="black")

    # 막대 위에 각 구간의 개수를 숫자로 적는다
    for count, patch in zip(counts, patches):
        ax.text(
            patch.get_x() + patch.get_width() / 2,
            patch.get_height(),
            str(int(count)),
            ha="center",
            va="bottom",
        )

    # 가로축 제목을 붙인다 (그림 안 글자는 모두 영어로: 회 -> per-visit, 월 -> per-month)
    unit_label_en = "per-visit" if unit == "회" else "per-month"
    ax.set_xlabel(f"Price (KRW, {unit_label_en})")

    # 세로축 제목을 붙인다
    ax.set_ylabel("Number of gyms")

    # 그래프 제목에 실제 행 수(n)를 넣는다 (그림 안 글자는 영어로 표기)
    ax.set_title(f"price_unit = {unit_label_en} (n = {len(sub)})")

    # 가로축 눈금을 구간 경계 값으로 지정한다
    ax.set_xticks(bin_edges)

    # x축 눈금이 겹치지 않도록 회전한다
    ax.tick_params(axis="x", rotation=45)

    # 이 단위의 결과를 나중에 표로 출력하기 위해 저장한다
    results_by_unit[unit] = (bin_edges, counts, len(sub))

# 전체 그림 제목을 붙인다
fig.suptitle("Da-gym Seoul Yoga listings, price by unit (hoe vs wol)")

# 그래프끼리 겹치지 않도록 여백을 정리한다
fig.tight_layout()

# charts 폴더가 없으면 만들어 둔다
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# 그래프를 파일로 저장한다 (화면 표시는 하지 않는다)
fig.savefig(OUTPUT_PATH)

print("저장 완료:", OUTPUT_PATH)
print()

# 단위별로 구간 빈도 표와 합계/비교를 출력한다
for unit in ["회", "월"]:
    bin_edges, counts, unit_rows = results_by_unit[unit]

    print(f"=== price_unit = {unit} ===")
    print("| 구간 | 개수 |")
    print("|---|---|")

    for i in range(len(bin_edges) - 1):
        left = bin_edges[i]
        right = bin_edges[i + 1]
        # 마지막 구간만 오른쪽 끝을 포함하므로 표기를 다르게 한다
        if i == len(bin_edges) - 2:
            label = f"[{left}, {right}]"
        else:
            label = f"[{left}, {right})"
        print(f"| {label} | {counts[i]} |")

    # 빈도 합계를 구한다
    count_sum = int(counts.sum())
    print(f"| 합계 | {count_sum} |")

    # 빈도 합과 이 단위의 실제 행 수를 나란히 출력하고 같음/다름을 밝힌다
    match_result = "같음" if count_sum == unit_rows else "다름"
    print(f"빈도 합: {count_sum}  price_unit={unit} 행 수: {unit_rows}  -> {match_result}")
    print()

# 두 단위를 합친 개수와 clean.csv 전체 행 수를 나란히 출력하고 같음/다름을 밝힌다
combined_rows = results_by_unit["회"][2] + results_by_unit["월"][2]
combined_match = "같음" if combined_rows == total_rows else "다름"
print(f"회+월 행 수 합: {combined_rows}  clean.csv 전체 행 수: {total_rows}  -> {combined_match}")
