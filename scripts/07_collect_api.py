# 필요한 라이브러리를 불러온다
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from zoneinfo import ZoneInfo

# 개발자도구 Network 탭에서 확인한 실제 목록 API 주소
API_URL = "https://www.da-gym.co.kr/api/gyms"

# 상세 주소를 만들 때 기준이 되는 사이트 기본 주소 (M02에서 확인한 규칙: /detail/{_id})
BASE_URL = "https://www.da-gym.co.kr"

# 이 스크립트 파일 위치를 기준으로 저장 경로를 정의한다 (기존 raw.csv는 건드리지 않는다)
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "raw_api_full.csv"

# 개발자도구에서 확인한 요청 파라미터 (offset만 바꿔가며 반복 호출한다)
PARAMS_BASE = {
    "longitude": "127.0742595815513",
    "latitude": "37.550638892935346",
    "limit": 20,
    "keyword": "서울요가",
    "keyword_attr": "etc",
    "exerciseType": "",
    "period": "",
    "count": "2,",
    "price": "0,",
    "isDailyItem": "false",
    "isLowestPrice": "false",
    "isPeriod": "true",
    "isCount": "true",
    "etc": "",
    "hasGymCoupon": "false",
}

# API가 요구하는 요청 헤더 (개발자도구에서 확인한 값, 로그인 쿠키는 포함하지 않는다)
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "authorization": "0",
    "referer": "https://www.da-gym.co.kr/search-result/%EC%84%9C%EC%9A%B8%EC%9A%94%EA%B0%80?attr=etc",
    "user-agent": (
        "Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/153.0.0.0 Mobile Safari/537.36"
    ),
    "x-dagym-platform": "web",
}

# 한국 시간(Asia/Seoul) 기준 수집 시점을 한 번만 계산한다 (M02와 동일한 방식)
scraped_at = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")

# 모든 offset에서 모은 원본 항목을 담을 리스트
all_items = []

# offset 0부터 20씩 늘려가며, 결과가 0건이 되면 멈춘다
offset = 0
while True:
    # 첫 요청 전에는 대기하지 않고, 이후 요청 사이에는 1초씩 대기한다
    if offset > 0:
        time.sleep(1)

    params = dict(PARAMS_BASE, offset=offset)
    response = requests.get(API_URL, params=params, headers=HEADERS, timeout=15)
    status_code = response.status_code

    # 상태 코드가 200이 아니면 즉시 중단한다
    if status_code != 200:
        print(f"offset={offset}  상태코드 {status_code}  중단 (응답이 200이 아니다)")
        break

    payload = response.json()
    center_list = payload.get("result", {}).get("centerList", [])

    # 시설 목록이 0개이면 더 이상 다음 페이지가 없다는 뜻이라 중단한다
    if len(center_list) == 0:
        print(f"offset={offset}  상태코드 {status_code}  0건  중단 (다음 목록이 없다)")
        break

    print(f"offset={offset}  상태코드 {status_code}  {len(center_list)}건")
    all_items.extend(center_list)
    offset += 20

print("누적 수집 항목 수:", len(all_items))
print()

# API 응답 한 건을 raw.csv와 같은 열 구조(문자열 원문)의 행으로 바꾼다
def item_to_row(item):
    gym_id = item.get("_id", "")
    detail_url = f"{BASE_URL}/detail/{gym_id}" if gym_id else ""

    name = item.get("name") or item.get("gymName", "")

    # M01/M02와 동일하게 "원문 그대로" 열(location_raw/price_raw/rating_raw)을 채운다
    location_raw = item.get("address", "")

    price = item.get("price") or {}
    product_type = price.get("productType")
    dagym_price = price.get("dagymPrice")

    # productType이 "count"면 1회당 가격(회), "period"면 1개월당 가격(월)로 계산한다
    # (raw_p1.csv에 있던 실제 표시가와 대조해 확인한 규칙)
    price_raw = ""
    if product_type == "count" and dagym_price is not None and price.get("count"):
        per_unit = int(dagym_price / price["count"])
        price_raw = f"{per_unit:,}원~/회"
    elif product_type == "period" and dagym_price is not None and price.get("period"):
        per_unit = int(dagym_price / price["period"])
        price_raw = f"{per_unit:,}원~/월"

    review = item.get("review") or {}
    rate = review.get("rate")
    count = review.get("count")

    # 리뷰 수가 0이면 기존 데이터에서도 평점이 비어 있던 것과 같게 빈 값으로 둔다
    # API의 review.rate는 소수점이 긴 원값(예: 4.78)이라, 사이트 화면에 실제로 표시되는
    # 소수 첫째 자리 값(예: 4.8, raw_p1.csv에서 확인한 표기 방식)으로 반올림해 맞춘다
    rating_raw = ""
    if rate is not None and count:
        rounded_rate = round(rate, 1)
        rating_raw = f"{rounded_rate}({count})"

    return {
        "name": name,
        "location_raw": location_raw,
        "price_raw": price_raw,
        "rating_raw": rating_raw,
        "detail_url": detail_url,
        "scraped_at": scraped_at,
    }


rows = [item_to_row(item) for item in all_items]

df = pd.DataFrame(
    rows, columns=["name", "location_raw", "price_raw", "rating_raw", "detail_url", "scraped_at"]
)

# data 폴더가 없으면 만들어 둔다
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# CSV로 저장한다 (인덱스 제외, 한글 깨짐 방지용 utf-8-sig)
df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

print("저장 완료:", OUTPUT_PATH)
print("합계 행 수:", len(df))
print("서로 다른 detail_url 개수:", df["detail_url"].nunique())
