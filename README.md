# VapeCrawler

전자담배 제품을 위한 모듈식 웹 크롤러입니다. 이 프로젝트는 여러 이커머스 사이트에서 전자담배 제품 정보를 수집하기 위한 프레임워크를 제공합니다.

## 목차
- [특징](#특징)
- [요구사항](#요구사항)
- [설치방법](#설치방법)
- [사용방법](#사용방법)
- [프로젝트 구조](#프로젝트-구조)
- [새 크롤러 추가하기](#새-크롤러-추가하기)
- [결과 형식](#결과-형식)
- [문제해결](#문제해결)
- [라이센스](#라이센스)

## 특징

- 사이트별 크롤러 구현이 분리된 모듈식 아키텍처
- 여러 전자 담배 사이트 지원 (베이프몬스터, 김성유베이핑연구소, 액상24, 액상99, 쥬스박스, 액상샵, 스카이베이프, 키미베이프)
- Selenium Chrome 드라이버를 사용한 브라우저 자동화
- 특정 크롤러를 사용자 지정 매개변수로 실행하는 명령줄 인터페이스
- 카테고리별 크롤링 지원 (입호흡, 폐호흡)
- 제품 정보 추출
- 타임스탬프가 포함된 JSON 형식으로 결과 저장
- 헤드리스 모드 지원 (브라우저 창 없이 실행)
- 자동화된 데이터 수집 및 정렬 워크플로우
- Elasticsearch 기반 로깅 시스템

## 요구사항

- Python 3.6 이상
- ChromeDriver (Chrome 버전과 호환되는 버전)
- MariaDB/MySQL 데이터베이스
- 필수 Python 라이브러리:
  - selenium
  - pymysql
  - python-dotenv
  - Levenshtein
  - pykospacing
  - elasticsearch (로깅용)

## 설치방법

1. 리포지토리 복제:
   ```bash
   git clone https://github.com/yourusername/VapeCrawler.git
   cd VapeCrawler
   ```

2. 필요한 패키지 설치:
   ```bash
   pip install selenium pymysql python-dotenv Levenshtein pykospacing elasticsearch
   ```

3. Chrome과 ChromeDriver가 설치되어 있는지 확인:
    - Chrome 브라우저 설치: https://www.google.com/chrome/
    - ChromeDriver 다운로드: https://sites.google.com/a/chromium.org/chromedriver/downloads
      (Chrome 버전과 일치하는 ChromeDriver 버전을 다운로드하세요)
    - ChromeDriver가 PATH에 있거나 프로젝트 디렉토리에 있는지 확인

4. 환경 설정 파일 생성:
   `.env` 파일을 프로젝트 루트 디렉토리에 생성하고 다음과 같이 설정:
   ```
   MARIADB_HOST=
   MARIADB_USER=
   MARIADB_PASSWORD=
   MARIADB_DATABASE=
   ELASTICSEARCH_HOST=
   ELASTICSEARCH_PORT=
   ```

## 사용방법

### 기본 사용법

기본 설정으로 크롤러 실행 (모든 사이트에서 "vape" 제품 크롤링):
```bash
python VapeCrawler.py
```

### 특정 사이트 크롤링

특정 사이트만 크롤링:
```bash
python VapeCrawler.py --sites vapemonster
```

여러 사이트 지정:
```bash
python VapeCrawler.py --sites vapemonster vapinglab juice24
```

### 지원하는 사이트

- `vapemonster` - 베이프몬스터(베몬)
- `vapinglab` - 김성유베이핑연구소(김성유)
- `juice24` - 액상24
- `juice99` - 액상99
- `juicebox` - 쥬스박스
- `juiceshop` - 액상샵
- `skyvape` - 스카이베이프
- `kimivape` - 키미베이프

### 특정 키워드로 검색

특정 키워드로 제품 검색:
```bash
python VapeCrawler.py --keywords "pod" "liquid"
```

### 특정 카테고리 크롤링

각 사이트의 특정 카테고리만 크롤링:
```bash
python VapeCrawler.py --sites vapemonster --categories 입호흡 폐호흡
```

여러 사이트의 특정 카테고리 크롤링:
```bash
python VapeCrawler.py --sites vapemonster vapinglab juice24 --categories 입호흡 폐호흡
```

사용 가능한 카테고리:
- 입호흡
- 폐호흡

### 브라우저 창 표시 (디버깅용)

헤드리스 모드를 비활성화하여 브라우저 창을 표시:
```bash
python VapeCrawler.py --no-headless
```

### 환경 설정 파일 지정

특정 환경 설정 파일을 사용하여 실행:
```bash
python VapeCrawler.py --env-file .env.development
```

### 모든 옵션 조합

모든 옵션을 조합하여 사용:
```bash
python VapeCrawler.py --sites vapemonster --keywords "pod" --categories 입호흡 --no-headless --env-file .env.development
```

### VapeRunner 사용법

VapeRunner는 VapeCrawler와 VapeSort를 순차적으로 실행하고, 모든 작업이 완료된 후 로그 파일을 정리하는 자동화 스크립트입니다.

#### 기본 사용법

기본 설정으로 VapeRunner 실행:
```bash
python VapeRunner.py
```

#### 환경 설정 파일 지정

특정 환경 설정 파일을 사용하여 실행:
```bash
python VapeRunner.py --env-file .env.development
```

#### 주기적 실행 (N분 간격)

VapeRunner를 특정 시간 간격으로 반복 실행:
```bash
python VapeRunner.py --interval 60  # 60분(1시간)마다 실행
```

```bash
python VapeRunner.py --interval 30  # 30분마다 실행
```

```bash
python VapeRunner.py --env-file .env.development --interval 120  # 2시간마다 실행 (특정 환경 설정 파일 사용)
```

주기적 실행 모드에서는 Ctrl+C를 눌러 프로그램을 종료할 수 있습니다.

## 프로젝트 구조

```
VapeCrawler/
├── VapeCrawler.py         # 크롤링 메인 스크립트
├── VapeSort.py            # 크롤링 데이터 정렬 스크립트
├── VapeRunner.py          # 크롤링 및 정렬 자동화 스크립트
├── crawlers/              # 크롤러 모듈
│   ├── __init__.py        # 패키지 초기화
│   ├── base_crawler.py    # 기본 크롤러 클래스
│   ├── vapemonster_crawler.py  # VapeMonster 사이트용 크롤러
│   ├── vapinglab_crawler.py    # VapingLab 사이트용 크롤러
│   ├── juice24_crawler.py      # Juice24 사이트용 크롤러
│   ├── juice99_crawler.py      # Juice99 사이트용 크롤러 
│   ├── juicebox_crawler.py     # Juicebox 사이트용 크롤러
│   ├── juiceshop_crawler.py    # Juiceshop 사이트용 크롤러
│   ├── skyvape_crawler.py      # SkyVape 사이트용 크롤러
│   └── kimivape_crawler.py     # KimiVape 사이트용 크롤러
├── module/                # 유틸리티 모듈
│   ├── MariaDBConnector.py # 데이터베이스 연결 모듈
│   ├── elasticsearch_logger.py # Elasticsearch 로깅 모듈
│   └── logger.py          # 기본 로깅 모듈
├── results/               # 크롤링 결과 저장 디렉토리
│   └── *.json             # 크롤링 결과 JSON 파일
├── log/                   # 로그 디렉토리
│   ├── vape_crawler.log   # 크롤러 로그 파일
│   ├── vape_sort.log      # 정렬 로그 파일
│   └── vape_runner.log    # 자동화 실행 로그 파일
└── .env                   # 환경 설정 파일
```

## 새 크롤러 추가하기

1. `crawlers` 디렉토리에 새 크롤러 파일 생성 (예: `newsite_crawler.py`)
2. `BaseCrawler` 클래스를 상속받는 새 크롤러 클래스 구현:

```python
from .base_crawler import BaseCrawler

class NewSiteCrawler(BaseCrawler):
    def __init__(self, headless=True, category=None, env_file=None):
        super().__init__(headless=headless, env_file=env_file)
        self.site_name = 'newsite'
        self.site_url = 'https://www.newvapesite.com'
        self.category = category
    
    def crawl(self, keywords=None, categories=None):
        # 크롤링 로직 구현
        results = {"입호흡": [], "폐호흡": []}
        # ...
        return results
```

3. `crawlers/__init__.py`에 새 크롤러 클래스 추가:

```python
from .newsite_crawler import NewSiteCrawler
# ...existing imports...
__all__ = ['BaseCrawler', 'VapeMonsterCrawler', 'VapingLabCrawler', 'Juice24Crawler', 
           'Juice99Crawler', 'JuiceboxCrawler', 'JuiceshopCrawler', 'SkyVapeCrawler', 
           'KimiVapeCrawler', 'NewSiteCrawler']
```

4. `VapeCrawler.py`의 `crawler_map` 딕셔너리에 새 크롤러 추가:

```python
crawler_map = {
    'vapemonster': VapeMonsterCrawler,
    'vapinglab': VapingLabCrawler,
    'juice24': Juice24Crawler,
    'juice99': Juice99Crawler,
    'juicebox': JuiceboxCrawler,
    'juiceshop': JuiceshopCrawler,
    'skyvape': SkyVapeCrawler,
    'kimivape': KimiVapeCrawler,
    'newsite': NewSiteCrawler
}
```

5. 명령줄 인수 파서에 새 사이트 옵션 추가:

```python
parser.add_argument('--sites', nargs='+', 
                   choices=['vapemonster', 'vapinglab', 'juice24', 'juice99', 
                           'juicebox', 'juiceshop', 'skyvape', 'kimivape', 
                           'newsite', 'all'], 
                   default=['all'],
                   help='Sites to crawl (default: all)')
```

## 결과 형식

크롤링 결과는 `results` 디렉토리에 JSON 파일로 저장됩니다. 파일 이름은 `{site_name}_{timestamp}.json` 형식입니다.

### 크롤링 결과 예시:
```json
{
  "입호흡": [
    {
      "title": "제품 이름",
      "detail_comment": "제품 설명",
      "price": 10500,
      "url": "https://www.example-site.com/product/1234",
      "image_url": "https://example.com/image.png"
    },
    // 더 많은 제품...
  ],
  "폐호흡": [
    // 다른 카테고리의 제품들...
  ]
}
```

## 데이터베이스 구조

이 프로젝트는 MariaDB/MySQL 데이터베이스를 사용하여 제품 정보와 가격 변동 이력을 저장합니다. 주요 테이블은 다음과 같습니다:

1. `vape_products` - 제품 정보
   - id, companyId, productCategoryId, visibleName, productGroupingName, imageUrl 등

2. `vape_price_comparisons` - 현재 가격 정보
   - id, productId, sellerId, sellerUrl, price 등

3. `vape_price_history` - 가격 변동 이력
   - productId, sellerId, oldPrice, newPrice, priceDifference, percentageChange, createdAt 등

4. `vape_company` - 제조사 정보
   - id, name 등

5. `vape_seller_site` - 판매 사이트 정보
   - id, name 등

6. `vape_product_category` - 제품 카테고리 정보
   - id, name 등

## 문제해결

### ChromeDriver 관련 문제
- **오류**: "ChromeDriver executable needs to be in PATH"
  - **해결**: ChromeDriver가 PATH에 있는지 확인하거나, ChromeDriver 경로를 명시적으로 지정

### 데이터베이스 연결 문제
- **오류**: "Connection refused" 또는 "Access denied"
  - **해결**: `.env` 파일의 데이터베이스 연결 정보가 올바른지 확인

### 크롤링 문제
- **오류**: 특정 사이트 크롤링 실패
  - **해결**: 해당 크롤러의 셀렉터가 변경되었는지 확인하고 업데이트

### 로깅 문제
- **오류**: Elasticsearch 로깅 실패
  - **해결**: Elasticsearch 서버가 실행 중인지 확인하고 `.env` 파일 설정 확인

## 라이센스
이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 LICENSE 파일을 참조하세요.
