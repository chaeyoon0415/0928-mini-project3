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
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "charts" / "hist.png"

# clean.csv를 읽기만 한다 (원본은 수정하지 않는다)
df = pd.read_csv(INPUT_PATH, encoding="utf-8-sig")

# 실제 price 값 범위(5,925원~112,750원)에 맞춘 구간 경계를 정의한다
bin_edges = [0, 20000, 40000, 60000, 80000, 100000, 120000]

# clean.csv 전체 행 수를 구한다 (제목의 n에 사용)
total_rows = len(df)

# numpy.histogram으로 구간별 개수를 센다
# (왼쪽 끝 포함·오른쪽 끝 미포함이 기본이며, 마지막 구간만 양쪽 끝을 포함한다)
counts, edges = np.histogram(df["price"], bins=bin_edges)

# 그림 크기를 지정해 새 그래프를 만든다
fig, ax = plt.subplots(figsize=(8, 5))

# 히스토그램 막대를 그린다 (구간 경계는 위에서 정의한 값을 그대로 사용)
n_out, bins_out, patches = ax.hist(df["price"], bins=bin_edges, edgecolor="black")

# 막대 위에 각 구간의 개수를 숫자로 적는다
for count, patch in zip(counts, patches):
    ax.text(
        patch.get_x() + patch.get_width() / 2,
        patch.get_height(),
        str(int(count)),
        ha="center",
        va="bottom",
    )

# 가로축 제목을 붙인다
ax.set_xlabel("Price (KRW)")

# 세로축 제목을 붙인다
ax.set_ylabel("Number of gyms")

# 그래프 제목에 실제 행 수(n)를 넣는다
ax.set_title(f"Da-gym Seoul Yoga listings, search page 1 (n = {total_rows})")

# 가로축 눈금을 구간 경계 값으로 지정한다
ax.set_xticks(bin_edges)

# charts 폴더가 없으면 만들어 둔다
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# 그래프를 파일로 저장한다 (화면 표시는 하지 않는다)
fig.savefig(OUTPUT_PATH)

print("저장 완료:", OUTPUT_PATH)
print()

# 구간별 빈도 표를 마크다운 표 형식으로 출력한다
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
print()

# 빈도 합과 clean.csv 전체 행 수를 나란히 출력하고 같음/다름을 밝힌다
match_result = "같음" if count_sum == total_rows else "다름"
print(f"빈도 합: {count_sum}  clean.csv 전체 행 수: {total_rows}  -> {match_result}")
