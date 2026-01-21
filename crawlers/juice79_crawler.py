"""
79juice 크롤러 구현.
"""
from .base_crawler import BaseCrawler


class Juice79Crawler(BaseCrawler):
    """
    79juice 웹사이트용 크롤러.
    """

    # 카테고리 URL 매핑
    CATEGORIES = {
        "입호흡": "/category/%EC%9E%85%ED%98%B8%ED%9D%A1-%EC%95%A1%EC%83%81/45/",
        "폐호흡": "/category/%ED%8F%90%ED%98%B8%ED%9D%A1-%EC%95%A1%EC%83%81/46/",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("juice79", headless, env_file=env_file)
        self.base_url = "https://79juice.co.kr"
        self.category = category
        self.category_url = f"{self.base_url}{self.CATEGORIES.get(category, self.CATEGORIES['입호흡'])}"

    def get_products(self):
        """
        79juice에서 제품을 가져옵니다.
        """
        selectors = {
            "list": ".xans-product-listnormal .prdList [id^='anchorBoxId_']",
            "title": ".description .name a",
            "price": [
                ".description .prd_price_sale span:nth-child(2)",
                ".description .product_price"
            ],
            "url": ".thumbnail a",
            "sold_out": "img[alt='품절']"
        }
        return self.get_products_by_selectors(selectors)