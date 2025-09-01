"""
모두의액상(everyonevape) 크롤러 구현.
사이트: https://xn--hu1b83j3sfk9e3xc.kr/
요구사항: 제공된 API를 호출하여 JSON 결과를 생성 (브라우저 자동화 불필요).
"""
import json
import time
from urllib.parse import urljoin

from .base_crawler import BaseCrawler


class EveryoneVapeCrawler(BaseCrawler):
    """
    Cafe24 ApiProductNormal JSON API를 이용하여 제품을 수집합니다.
    카테고리:
      - 입호흡 cate_no=127
      - 폐호흡 cate_no=123
    """

    SITE_KO = "모두의액상"
    BASE_HOST = "https://xn--hu1b83j3sfk9e3xc.kr"
    API_TEMPLATE = (
            BASE_HOST +
            "/exec/front/Product/ApiProductNormal?cate_no={cate_no}&supplier_code=S0000000&page={page}&bInitMore=F&count=200"
    )

    CATEGORIES = {
        "입호흡": 127,
        "폐호흡": 123,
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        # BaseCrawler는 Selenium 드라이버를 초기화하지만, 이 크롤러는 API만 사용하므로
        # headless, driver는 유지하되 driver는 사용하지 않습니다.
        super().__init__("everyonevape", headless, env_file=env_file)
        self.category = category

    def _fetch_api(self, cate_no, page=1):
        url = self.API_TEMPLATE.format(cate_no=cate_no, page=page)
        # Selenium을 사용해도 되지만 간단히 driver.get으로 네트워크 요청을 유발하고
        # 페이지 소스로 JSON을 읽을 수 없으므로, 여기서는 requests 없이도 동작하도록
        # JavaScript fetch를 사용할 수 없기에 Selenium 없이 표준 라이브러리를 사용하지 않는 것이 제약.
        # 프로젝트 내 다른 크롤러들은 Selenium 기반이므로, 여기서는 driver.get(url) 후 body 텍스트를 가져오는 방식 사용.
        try:
            if not self.navigate_to(url):
                return None
            time.sleep(1)
            # Cafe24 API는 text/plain JSON 응답을 반환하므로, page_source에 JSON 문자열이 포함됩니다.
            # Selenium의 page_source에는 HTML wrapper가 없고 순수 JSON이 들어오는 경우가 많습니다.
            src = self.driver.page_source
            # 일부 드라이버는 <pre> 태그로 감싸 반환하기도 하므로 양쪽의 태그를 제거
            # JSON 시작 위치와 끝 위치를 찾아서 슬라이스
            start = src.find('{')
            end = src.rfind('}')
            if start != -1 and end != -1 and end > start:
                json_text = src[start:end + 1]
                return json.loads(json_text)
        except Exception as e:
            self.logger.error(f"API 응답 파싱 실패: {str(e)}")
        return None

    @staticmethod
    def _ensure_http(url, base):
        if not url:
            return ""
        if url.startswith("http://") or url.startswith("https://"):
            return url
        # 스킴이 없는 경우 호스트와 결합
        return "https:" + url

    def get_products(self, cate_no):
        products = []
        page = 1
        max_pages = 20
        while page <= max_pages:
            data = self._fetch_api(cate_no, page=page)
            if not data:
                break
            try:
                items = data.get('rtn_data', {}).get('data', [])
            except Exception as e:
                self.logger.error(f"API 데이터 파싱 오류: {str(e)}")
                items = []

            # 데이터가 없으면 페이징 종료
            if not items:
                self.logger.info(f"cate_no={cate_no} page={page}: 더 이상 데이터 없음, 종료")
                break

            for item in items:
                try:
                    is_sold_out = item.get('soldout_icon') or ""
                    if is_sold_out != "":
                        continue

                    title = item.get('disp_product_name') or ""
                    image = item.get('image_small') or ""
                    detail = item.get('link_product_detail') or ""
                    price = item.get('product_price')
                    try:
                        price_int = int(str(price).replace(',', '').strip()) if price is not None else 0
                    except Exception as e:
                        self.logger.error(f"상품 가격 파싱 오류: {str(e)}")
                        continue

                    if title == "" or detail == "":
                        continue

                    image_url = ""
                    if image:
                        image_url = self._ensure_http(image, self.BASE_HOST)

                    products.append({
                        "title": title,
                        "price": price_int,
                        "url": self.BASE_HOST + "/" + detail,
                        "image_url": image_url,
                        "detail_comment": ""
                    })
                except Exception as e:
                    self.logger.error(f"제품 변환 오류: {str(e)}")

            page += 1
        return products

    def crawl(self, keywords=None, categories=None):
        self.logger.info(f"{self.SITE_KO} 크롤링 시작 (API 기반)")
        results = {}
        if categories is None:
            categories = list(self.CATEGORIES.keys())
        for cat in categories:
            cate_no = self.CATEGORIES.get(cat)
            if cate_no is None:
                continue
            self.logger.info(f"카테고리 '{cat}' 데이터 수집 (cate_no={cate_no})")
            products = self.get_products(cate_no)
            results[cat] = products
            self.logger.info(f"카테고리 '{cat}'에서 {len(products)}개 제품 발견")
        return results
