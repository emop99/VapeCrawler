"""
99주스 크롤러 구현.
"""
from .base_crawler import BaseCrawler


class Juice99Crawler(BaseCrawler):
    """
    99주스 웹사이트용 크롤러.
    """

    # 카테고리 URL 매핑
    CATEGORIES = {
        "입호흡": "/category/입호흡-액상/42/",
        "폐호흡": "/category/폐호흡-액상/43/",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("juice99", headless, env_file=env_file)
        self.base_url = "https://99juice.co.kr"
        self.category = category
        self.category_url = f"{self.base_url}{self.CATEGORIES.get(category, self.CATEGORIES['입호흡'])}"

    def get_products(self):
        """
        99주스에서 제품을 가져옵니다.
        """
        selectors = {
            "list": ".sp-product-item",
            "title": ".sp-product-name",
            "price": ".sp-product-spec div[rel='판매가']",
            "url": ".sp-product-item-thumb a",
            "image": ".sp-product-item-thumb img",
            "sold_out": "img[alt='품절']"
        }
        return self.get_products_by_selectors(selectors)
