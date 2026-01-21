"""
시가누리(ciganuri) 크롤러 구현.
사이트: https://xn--o39a37i99gz8j.com

Cafe24 기반 사이트와 유사한 리스트 셀렉터를 사용합니다.
카테고리:
  - 입호흡: https://xn--o39a37i99gz8j.com/product/list.html?cate_no=73
  - 폐호흡: https://xn--o39a37i99gz8j.com/product/list.html?cate_no=74
페이징: page 파라미터 사용
"""
from .base_crawler import BaseCrawler


class CiganuriCrawler(BaseCrawler):
    """
    시가누리 웹사이트용 크롤러.
    Cafe24 기반 레이아웃과 동일한 셀렉터 패턴을 사용.
    """

    CATEGORIES = {
        "입호흡": "73",
        "폐호흡": "74",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("ciganuri", headless, env_file=env_file)
        self.base_url = "https://xn--o39a37i99gz8j.com"
        self.category = category
        self.category_url = f"{self.base_url}/product/list.html?cate_no={self.CATEGORIES.get(category, self.CATEGORIES['입호흡'])}"

    def get_products(self):
        """
        시가누리에서 제품을 가져옵니다.
        """
        selectors = {
            "list": ".xans-product-listnormal .prdList [id^='anchorBoxId_']",
            "title": ".description .name span:nth-child(2)",
            "price": [
                ".description ul.spec li[column_name='prd_price_sale'] span:nth-child(2)",
                ".description ul.spec li[column_name='product_price'] span:nth-child(2)",
            ],
            "url": "div.thumbnail a",
            "image": "div.thumbnail a img",
            "sold_out": "img[alt='품절']"
        }
        return self.get_products_by_selectors(selectors)
