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
        super().__init__("everyonevape", headless, env_file=env_file)
        self.base_url = self.BASE_HOST
        self.category = category

    def _fetch_api(self, cate_no, page=1):
        url = self.API_TEMPLATE.format(cate_no=cate_no, page=page)
        try:
            if not self.navigate_to(url):
                return None
            time.sleep(1)
            src = self.driver.page_source
            start = src.find('{')
            end = src.rfind('}')
            if start != -1 and end != -1 and end > start:
                json_text = src[start:end + 1]
                return json.loads(json_text)
        except Exception as e:
            self.logger.error(f"API 응답 파싱 실패: {str(e)}")
        return None

    def get_products(self):
        cate_no = self.CATEGORIES.get(self.category)
        if not cate_no:
            return []

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

            if not items:
                break

            for item in items:
                try:
                    if item.get('soldout_icon'):
                        continue

                    title = item.get('disp_product_name') or ""
                    image = item.get('image_small') or ""
                    detail = item.get('link_product_detail') or ""
                    price = self.parse_price(str(item.get('product_price', 0)))

                    if title == "" or detail == "":
                        continue

                    image_url = ""
                    if image:
                        image_url = image if image.startswith("http") else "https:" + image

                    products.append({
                        "title": title,
                        "price": price,
                        "url": urljoin(self.BASE_HOST, detail),
                        "image_url": image_url,
                        "detail_comment": ""
                    })
                except Exception as e:
                    self.logger.error(f"제품 변환 오류: {str(e)}")

            page += 1
        return products
