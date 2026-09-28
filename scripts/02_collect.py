# 필요한 라이브러리를 불러온다
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from zoneinfo import ZoneInfo

# 다짐은 무한 스크롤 방식이라 페이지 번호 대신, 개발자도구에서 확인한
# API(limit/offset)를 이용해 20개씩 묶어서 수집한다
API_URL = "https://www.da-gym.co.kr/api/gyms"

# 상세 주소를 만들 때 기준이 되는 사이트 기본 주소 (M02에서 확인한 규칙: /detail/{_id})
BASE_URL = "https://www.da-gym.co.kr"

# 이 스크립트 파일 위치를 기준으로 저장 경로를 정의한다
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "raw.csv"

# 개발자도구에서 확인한 요청 조건
LIMIT = 20
KEYWORD = "요가"

# 처음 20개 -> offset=20 -> offset=40 순서로, 최대 3묶음까지만 수집한다
OFFSETS = [0, 20, 40]

# 누적 행 수가 이 값 이상이 되면 그 묶음까지만 저장하고 멈춘다
ROW_LIMIT = 50

# 한국 시간(Asia/Seoul) 기준 수집 시점을 한 번만 계산한다 (M02와 동일한 방식)
scraped_at = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")

# 모든 묶음에서 모은 행을 담을 리스트
all_rows = []

# 어느 offset에서 멈췄는지 기록해 둘 변수 (정상 종료면 None)
stopped_at_offset = None

# location_raw/price_raw/rating_raw를 API에서 바로 얻지 못했다는 사실을 한 번만 출력하기 위한 표시
missing_fields_notice_printed = False

for i, offset in enumerate(OFFSETS):
    # 묶음 사이에는 1초씩 대기한다 (첫 요청 전에는 대기하지 않는다)
    if i > 0:
        time.sleep(1)

    # API에 GET 요청을 보낸다
    response = requests.get(
        API_URL,
        params={"limit": LIMIT, "offset": offset, "keyword": KEYWORD},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15,
    )
    status_code = response.status_code

    # 상태 코드가 200이 아니면 즉시 중단한다
    if status_code != 200:
        print(f"offset={offset}  상태코드 {status_code}  중단 (응답이 200이 아니다)")
        stopped_at_offset = offset
        break

    # JSON 응답을 파싱한다
    payload = response.json()
    center_list = payload.get("result", {}).get("centerList", [])

    # 시설 목록이 0개이면 즉시 중단한다
    if len(center_list) == 0:
        print(f"offset={offset}  상태코드 {status_code}  0행  중단 (시설 목록이 비어 있다)")
        stopped_at_offset = offset
        break

    # 이번 묶음에서 뽑아낼 행을 담을 리스트
    batch_rows = []

    for item in center_list:
        # 시설 ID로 상세 주소를 만든다 (M02에서 확인한 상세 URL 규칙 그대로 사용)
        gym_id = item.get("_id", "")
        detail_url = f"{BASE_URL}/detail/{gym_id}" if gym_id else ""

        # API 응답에 바로 있는 이름만 그대로 가져온다 (없으면 빈 값)
        name = item.get("name", "")

        # location_raw/price_raw/rating_raw는 M02의 HTML 추출 방식으로 얻은 값이라
        # API 응답만으로는 동일한 방식으로 재현할 수 없다 -> 임의 계산하지 않고 빈 값으로 둔다
        location_raw = ""
        price_raw = ""
        rating_raw = ""

        batch_rows.append(
            {
                "name": name,
                "location_raw": location_raw,
                "price_raw": price_raw,
                "rating_raw": rating_raw,
                "detail_url": detail_url,
                "scraped_at": scraped_at,
            }
        )

    if not missing_fields_notice_printed:
        print(
            "안내: location_raw, price_raw, rating_raw는 API 응답에서 M02와 동일한 방식으로 "
            "얻을 수 없어 빈 값으로 남긴다"
        )
        missing_fields_notice_printed = True

    all_rows.extend(batch_rows)

    # 요청한 출력 형식대로 이번 묶음 결과를 출력한다
    print(f"offset={offset}  상태코드 {status_code}  {len(batch_rows)}행")

    # 누적 50행 이상이면 이 묶음까지 저장하고 멈춘다
    if len(all_rows) >= ROW_LIMIT:
        break

# 수집한 행을 M02와 동일한 열 이름/순서로 데이터프레임을 만든다
df = pd.DataFrame(
    all_rows,
    columns=["name", "location_raw", "price_raw", "rating_raw", "detail_url", "scraped_at"],
)

if len(df) == 0:
    # 한 행도 모으지 못했으면 지어내지 않고 그 사실만 출력한다
    print("수집된 행이 0개라 data/raw.csv를 만들지 않는다")
    if stopped_at_offset is not None:
        print(f"중단된 offset: {stopped_at_offset}")
else:
    # data 폴더가 없으면 만들어 둔다
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # CSV로 저장한다 (인덱스 제외, 한글 깨짐 방지용 utf-8-sig)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print("저장 완료:", OUTPUT_PATH)

    # 합계 행 수와 서로 다른 detail_url 개수를 출력한다
    print("합계 행 수:", len(df))
    print("서로 다른 detail_url 개수:", df["detail_url"].nunique())

    # 첫 행 / 가운데 행 / 마지막 행을 골라 행 번호와 모든 열을 출력한다
    first_idx = 0
    middle_idx = len(df) // 2
    last_idx = len(df) - 1

    for label, idx in [("첫 행", first_idx), ("가운데 행", middle_idx), ("마지막 행", last_idx)]:
        print(f"--- {label} (행 번호 {idx}) ---")
        print(df.iloc[idx])
