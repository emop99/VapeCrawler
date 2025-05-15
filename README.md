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
- 여러 전자 담배 사이트 지원
- Selenium Chrome 드라이버를 사용한 브라우저 자동화
- 특정 크롤러를 사용자 지정 매개변수로 실행하는 명령줄 인터페이스
- 카테고리별 크롤링 지원
- 제품 정보 추출
- 타임스탬프가 포함된 JSON 형식으로 결과 저장
- 헤드리스 모드 지원 (브라우저 창 없이 실행)

## 요구사항

- Python 3.6 이상
- ChromeDriver (Chrome 버전과 호환되는 버전)
- Selenium 라이브러리

## 설치방법

1. 리포지토리 복제:
   ```bash
   git clone https://github.com/yourusername/VapeCrawler.git
   cd VapeCrawler
   ```

2. 필요한 패키지 설치:
   ```bash
   pip install selenium
   ```

3. Chrome과 ChromeDriver가 설치되어 있는지 확인:
    - Chrome 브라우저 설치: https://www.google.com/chrome/
    - ChromeDriver 다운로드: https://sites.google.com/a/chromium.org/chromedriver/downloads
      (Chrome 버전과 일치하는 ChromeDriver 버전을 다운로드하세요)
    - ChromeDriver가 PATH에 있거나 프로젝트 디렉토리에 있는지 확인

## 사용방법

### 기본 사용법

기본 설정으로 크롤러 실행 (모든 사이트에서 "vape" 제품 크롤링):
```bash
python VapeCrawler.py
```

### 특정 사이트 크롤링

VapeMonster 사이트만 크롤링:
```bash
python VapeCrawler.py --sites vapemonster
```

VapingLab 사이트만 크롤링:
```bash
python VapeCrawler.py --sites vapinglab
```

### 특정 키워드로 검색

특정 키워드로 제품 검색:
```bash
python VapeCrawler.py --keywords "pod" "liquid"
```

### 특정 카테고리 크롤링

각 사이트의 특정 카테고리만 크롤링할 수 있습니다:

#### VapeMonster 카테고리 크롤링:
```bash
python VapeCrawler.py --sites vapemonster --categories 입호흡 폐호흡
```

#### VapingLab 카테고리 크롤링:
```bash
python VapeCrawler.py --sites vapinglab --categories 입호흡 폐호흡
```

#### Juice24 카테고리 크롤링:
```bash
python VapeCrawler.py --sites juice24 --categories 입호흡 폐호흡
```

#### 여러 사이트의 특정 카테고리 크롤링:
```bash
python VapeCrawler.py --sites vapemonster vapinglab juice24 --categories 입호흡 폐호흡
```

사용 가능한 카테고리:
- 입호흡
- 폐호흡
- 무니코틴 (베이프몬스터 한정)

### 브라우저 창 표시 (디버깅용)

헤드리스 모드를 비활성화하여 브라우저 창을 표시:
```bash
python VapeCrawler.py --no-headless
```

### 모든 옵션 조합

모든 옵션을 조합하여 사용:
```bash
python VapeCrawler.py --sites vapemonster --keywords "pod" --categories 입호흡 --no-headless
```

여러 사이트와 카테고리를 동시에 크롤링:
```bash
python VapeCrawler.py --sites vapemonster vapinglab --keywords "pod" "liquid" --categories 입호흡 폐호흡 --no-headless
```

## 프로젝트 구조

```
VapeCrawler/
├── VapeCrawler.py         # 메인 스크립트 (진입점)
├── crawlers/              # 크롤러 모듈
│   ├── __init__.py        # 패키지 초기화
│   ├── base_crawler.py    # 기본 크롤러 클래스
│   ├── vapemonster_crawler.py  # VapeMonster 사이트용 크롤러
│   ├── vapinglab_crawler.py    # VapingLab 사이트용 크롤러
│   └── juice24_crawler.py      # Juice24 사이트용 크롤러
├── results/               # 크롤링 결과 저장 디렉토리
│   ├── vapemonster_*.json # VapeMonster 크롤링 결과
│   ├── vapinglab_*.json   # VapingLab 크롤링 결과
│   └── juice24_*.json     # Juice24 크롤링 결과
└── vape_crawler.log       # 로그 파일
```

## 새 크롤러 추가하기

1. `crawlers` 디렉토리에 새 크롤러 파일 생성 (예: `newsite_crawler.py`)
2. `BaseCrawler` 클래스를 상속받는 새 크롤러 클래스 구현:
3. `crawlers/__init__.py`에 새 크롤러 클래스 추가:

```python
from .newsite_crawler import NewSiteCrawler
__all__ = ['BaseCrawler', 'VapeMonsterCrawler', 'VapingLabCrawler', 'NewSiteCrawler']
```

4. `VapeCrawler.py`의 `crawler_map` 딕셔너리에 새 크롤러 추가:

```python
crawler_map = {
    'vapemonster': VapeMonsterCrawler,
    'vapinglab': VapingLabCrawler,
    'newsite': NewSiteCrawler
}
```

5. 명령줄 인수 파서에 새 사이트 옵션 추가:

```python
parser.add_argument('--sites', nargs='+', choices=['vapemonster', 'vapinglab', 'newsite', 'all'], default=['all'],
                    help='Sites to crawl (default: all)')
```

6. 필요한 경우 카테고리 옵션에 새 카테고리 추가:

```python
parser.add_argument('--categories', nargs='+', choices=['입호흡', '폐호흡', '무니코틴', '카테고리1', '카테고리2'],
                    help='Categories to crawl')
```

## 결과 형식

크롤링 결과는 `results` 디렉토리에 JSON 파일로 저장됩니다. 파일 이름은 `{site_name}_{timestamp}.json` 형식입니다.

### VapeMonster 크롤링 결과 예시:
```json
{
  "입호흡": [
    {
      "title": "제품 이름",
      "detail_comment": "제품 설명",
      "price": 10500,
      "url": "https://www.vapemonster.co.kr/goods/goods_view.php?goodsNo=1000001234",
      "image_url": "https://example.com/image.png"
    },
    // 더 많은 제품...
  ],
  "폐호흡": [
    // 다른 카테고리의 제품들...
  ],
  "무니코틴": [
    // 다른 카테고리의 제품들...
  ]
}
```

### VapingLab 크롤링 결과 예시:
```json
{
  "입호흡": [
    {
      "title": "키슈 플럼 레거시 / 키슈 우메 매실주 (30ml, 9.9mg)",
      "detail_comment": "",
      "price": 19500,
      "url": "https://vapinglab.co.kr/product/kishuplumlegacy",
      "image_url": "https://contents.sixshop.com/thumbnails/uploadedFiles/113061/product/image_1725415110626_1000.jpg"
    },
    // 더 많은 제품...
  ],
  "폐호흡": [
    // 다른 카테고리의 제품들...
  ]
}
```

## 라이센스
이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 LICENSE 파일을 참조하세요.
