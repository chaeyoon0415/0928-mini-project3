# 필요한 라이브러리를 불러온다
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo

# 수집할 목록 페이지 주소를 정의한다
LIST_URL = "https://www.da-gym.co.kr/search-result/서울요가"

# 카드 링크가 href로 노출되지 않아 urljoin 기준이 되는 사이트 기본 주소를 정의한다
BASE_URL = "https://www.da-gym.co.kr"

# 이 스크립트 파일 위치를 기준으로 저장 경로를 정의한다
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "raw_p1.csv"

# 목록 페이지 하나만 요청한다 (상세 페이지는 요청하지 않는다)
response = requests.get(LIST_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)

# 응답 인코딩을 페이지에 맞춰 준다 (모르면 utf-8)
response.encoding = response.encoding or "utf-8"

# 응답 상태 코드를 출력한다
print("status_code:", response.status_code)

# 200이 아니면 이후 처리를 중단한다
if response.status_code != 200:
    print("응답 상태 코드가 200이 아니라 CSV를 만들지 않는다")
else:
    # BeautifulSoup으로 HTML을 파싱한다
    soup = BeautifulSoup(response.text, "html.parser")

    # 목록 카드마다 시설 상세 주소(url)를 미리 매핑해 둘 딕셔너리를 만든다
    name_to_url = {}

    # 페이지에 포함된 JSON-LD(구조화 데이터) 스크립트를 모두 찾는다
    ld_scripts = soup.find_all("script", type="application/ld+json")

    # JSON-LD 안에서 시설명과 상세 주소(url) 목록을 뽑아 매핑을 채운다
    import json

    for script in ld_scripts:
        try:
            payload = json.loads(script.string)
        except (TypeError, ValueError):
            continue
        graph = payload.get("@graph", []) if isinstance(payload, dict) else []
        for node in graph:
            main_entity = node.get("mainEntity") if isinstance(node, dict) else None
            if not isinstance(main_entity, dict):
                continue
            for element in main_entity.get("itemListElement", []):
                item = element.get("item", {})
                item_name = item.get("name")
                item_url = item.get("url")
                if item_name and item_url:
                    name_to_url[item_name] = item_url

    # 목록 한 칸(카드)의 반복 컨테이너를 클래스로 찾는다
    cards = soup.find_all(
        "div", class_="flex flex-col w-full cursor-pointer gap-4 bg-white px-narrow group"
    )

    # 각 카드에서 뽑아낼 값을 담을 리스트를 준비한다
    rows = []

    # 한국 시간(Asia/Seoul) 기준 수집 시점을 한 번만 계산한다
    scraped_at = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")

    # 카드 하나씩 순회하며 값을 그대로 추출한다
    for card in cards:
        # 시설명은 group-hover:!text-primary 클래스를 가진 span에서 가져온다
        name_tag = card.find("span", class_="group-hover:!text-primary")
        name = name_tag.get_text(strip=True) if name_tag else ""

        # 지역·주소 정보는 '•' 글자를 포함한 span에서 화면 글자 그대로 가져온다
        location_tag = card.find("span", string=re.compile("•"))
        location_raw = location_tag.get_text(strip=True) if location_tag else ""

        # 가격은 items-baseline 컨테이너의 글자를 그대로 이어붙여 가져온다
        price_tag = card.find("div", class_="flex flex-row shrink-0 items-baseline")
        price_raw = price_tag.get_text(strip=True) if price_tag else ""

        # 평점은 svg 아이콘이 있는 별점 묶음의 글자를 그대로 가져온다
        rating_raw = ""
        category_row = card.find("div", class_="flex flex-row items-center justify-between")
        if category_row is not None:
            rating_box = category_row.find("div", class_="flex flex-row items-center")
            if rating_box is not None and rating_box.find("svg") is not None:
                rating_raw = rating_box.get_text(strip=True)

        # JSON-LD 매핑에서 시설명으로 상세 주소를 찾고 urljoin으로 전체 주소를 만든다
        detail_url = urljoin(BASE_URL, name_to_url.get(name, ""))

        # 한 시설의 값을 행으로 모은다
        rows.append(
            {
                "name": name,
                "location_raw": location_raw,
                "price_raw": price_raw,
                "rating_raw": rating_raw,
                "detail_url": detail_url,
                "scraped_at": scraped_at,
            }
        )

    # 수집한 행들을 데이터프레임으로 만든다
    df = pd.DataFrame(rows, columns=["name", "location_raw", "price_raw", "rating_raw", "detail_url", "scraped_at"])

    # 수집된 행 수를 출력한다
    print("행 수:", len(df))

    # 앞 3행을 출력한다
    print(df.head(3))

    # 행이 0개면 CSV를 만들지 않는다
    if len(df) == 0:
        print("행 수가 0이라 CSV를 만들지 않는다")
    else:
        # data 폴더가 없으면 만들어 둔다
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

        # CSV로 저장한다 (인덱스 제외, 한글 깨짐 방지용 utf-8-sig)
        df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

        # 저장 경로를 출력한다
        print("저장 완료:", OUTPUT_PATH)
