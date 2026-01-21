"""
haoma111.cafe24.com(베이핑덕) 크롤러 구현.
"""
from .base_crawler import BaseCrawler

class VapeingduckCrawler(BaseCrawler):
    """
    베이핑덕 웹사이트용 크롤러.
    """
    CATEGORIES = {
        "입호흡": "/category/입호흡/58/",
        "폐호흡": "/category/폐호흡/59/",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("vapeingduck", headless, env_file=env_file)
        self.base_url = "https://haoma111.cafe24.com"
        self.category = category
        self.category_url = f"{self.base_url}{self.CATEGORIES.get(category, self.CATEGORIES['입호흡'])}"

    def get_products(self):
        """
        베이핑덕에서 제품을 가져옵니다.
        """
        selectors = {
            "list": ".prdList li.item",
            "title": ".description .name span:nth-child(2)",
            "price": ".description ul.spec li[rel='판매가'] span:nth-child(2)",
            "url": "div.thumbnail a",
            "image": "",
            "sold_out": "img[alt='품절']"
        }
        return self.get_products_by_selectors(selectors)