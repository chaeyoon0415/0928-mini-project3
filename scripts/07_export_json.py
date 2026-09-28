import pandas as pd  # csv를 표 형태(DataFrame)로 다루기 위해 pandas를 불러온다
import json  # json 파일을 직접 읽어서 검증할 때 사용한다

# 1) data/clean.csv 를 읽는다 (원본 csv는 수정하지 않고 읽기만 한다)
df = pd.read_csv("data/clean.csv")

# 2) 필요한 네 개 열만 선택한다: 이름, 가격, 평점, 상세페이지 주소
selected = df[["name", "price", "rating", "detail_url"]]

# 3) 한 행 = 한 딕셔너리 형태(records)의 리스트로 변환한다
records = selected.to_dict(orient="records")

# 4) data/data.json 으로 저장한다 (한글 깨짐 방지: ensure_ascii=False, 들여쓰기: indent=2)
with open("data/data.json", "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print("data.json 저장 완료")

# 5) 저장한 data.json 을 다시 읽어서 항목 수를 센다
with open("data/data.json", "r", encoding="utf-8") as f:
    loaded = json.load(f)

json_count = len(loaded)  # data.json 의 항목(레코드) 수
csv_count = len(df)  # clean.csv 의 데이터 행 수 (헤더 제외)

# 6) 항목 수와 행 수를 나란히 출력하고 같은지/다른지 적는다
print(f"data.json 항목 수: {json_count}")
print(f"clean.csv 행 수: {csv_count}")
print("같음" if json_count == csv_count else "다름")

# 7) data.json 첫 항목과 clean.csv 첫 줄의 네 값을 나란히 비교 출력한다
json_first = loaded[0]
csv_first = df.iloc[0][["name", "price", "rating", "detail_url"]].to_dict()

print("\n[data.json 첫 항목]")
print(json_first)
print("\n[clean.csv 첫 줄(네 값)]")
print(csv_first)
