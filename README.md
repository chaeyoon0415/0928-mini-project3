## 실행 안내

### 1. 다시 모으기

scripts 폴더의 파일을 번호 순서대로 실행합니다. (Windows는 `python`, Mac은 `python3`)

| 순서 | 파일 | 무엇을 만드는지 | 실행 명령 | 확인 여부 |
|---|---|---|---|---|
| 00 | scripts/00_env_check.py | 환경 확인용 가상 예시 표를 출력한다 (실제 수집이 아니다) | `python scripts/00_env_check.py` / `python3 scripts/00_env_check.py` | 확인 안 함 |
| 01 | scripts/01_collect_p1.py | 목록 페이지 1개를 수집해 data/raw_p1.csv를 만든다 — 사이트에 요청을 보낸다 · 페이지 수를 늘리지 않는다 | `python scripts/01_collect_p1.py` / `python3 scripts/01_collect_p1.py` | 확인 안 함 |
| 02 | scripts/02_collect.py | 목록 API를 offset 0·20·40 최대 3묶음까지 호출해 data/raw.csv를 만든다 — 사이트에 요청을 보낸다 · 페이지 수를 늘리지 않는다 | `python scripts/02_collect.py` / `python3 scripts/02_collect.py` | 확인 안 함 |
| 03 | scripts/03_clean.py | data/raw.csv를 정제해 data/clean.csv를 만든다 (필수값 빈칸·중복 행 제외) | `python scripts/03_clean.py` / `python3 scripts/03_clean.py` | 확인함 — 방금 실행: 오류 없이 끝남 · raw 38행 → 정제 24행 |
| 04 | scripts/04_stats.py | data/clean.csv의 price 열 통계(개수·최소·최대·평균·중앙값)를 출력한다 | `python scripts/04_stats.py` / `python3 scripts/04_stats.py` | 확인 안 함 |
| 05 | scripts/05_hist.py | data/clean.csv 전체 가격 히스토그램을 그려 charts/hist.png로 저장한다 | `python scripts/05_hist.py` / `python3 scripts/05_hist.py` | 확인 안 함 |
| 06 | scripts/06_by_category.py | price_unit(회/월)별 rating 평균 막대그래프를 그려 charts/by_category.png로 저장한다 | `python scripts/06_by_category.py` / `python3 scripts/06_by_category.py` | 확인 안 함 |
| 06 | scripts/06_hist_by_unit.py | price_unit(회/월)별로 나눈 가격 히스토그램을 그려 charts/hist_by_unit.png로 저장한다 | `python scripts/06_hist_by_unit.py` / `python3 scripts/06_hist_by_unit.py` | 확인 안 함 |
| 07 | scripts/07_collect_api.py | 목록 API를 offset 0부터 결과가 없어질 때까지 반복 호출해 data/raw_api_full.csv를 만든다 — 사이트에 요청을 보낸다 · 페이지 수를 늘리지 않는다 | `python scripts/07_collect_api.py` / `python3 scripts/07_collect_api.py` | 확인 안 함 |
| 07 | scripts/07_export_json.py | data/clean.csv에서 name·price·rating·detail_url 네 열만 뽑아 data/data.json을 만든다 | `python scripts/07_export_json.py` / `python3 scripts/07_export_json.py` | 확인 안 함 |

### 2. 화면에 반영하기

새로 만든 data/data.json과 charts 폴더 이미지를 커밋·푸시하면, Vercel이 이를 감지해 자동으로 다시 배포한다.

### 3. AI 연결

api/recommend.js는 Vercel 환경변수 `GEMINI_API_KEY`를 읽어 Gemini API를 호출한다. Vercel 프로젝트 설정에서 환경변수 이름 `GEMINI_API_KEY`에 열쇠 값을 넣고 Redeploy하면 적용된다. (열쇠 값 자체는 여기에 적지 않는다.)
