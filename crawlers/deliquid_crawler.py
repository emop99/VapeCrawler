"""
Deliquid crawler implementation.
Site: https://xn--hy1bte33lhv3a.com/
"""
from .base_crawler import BaseCrawler


class DeliquidCrawler(BaseCrawler):
    """
    Deliquid site crawler (Cafe24-based).
    """

    CATEGORIES = {
        "입호흡": "https://xn--hy1bte33lhv3a.com/category/%EC%9E%85%ED%98%B8%ED%9D%A1-%EC%95%A1%EC%83%81/43/",
        "폐호흡": "https://xn--hy1bte33lhv3a.com/category/%ED%8F%90%ED%98%B8%ED%9D%A1-%EC%95%A1%EC%83%81/44/",
    }

    def __init__(self, headless=True, category="입호흡", env_file=".env"):
        super().__init__("deliquid", headless, env_file=env_file)
        self.base_url = "https://xn--hy1bte33lhv3a.com"
        self.category = category
        self.category_url = self.CATEGORIES.get(category, self.CATEGORIES["입호흡"])

    def get_products(self):
        """
        Fetch product data from Deliquid category pages.
        """
        selectors = {
            "list": ".xans-product-listnormal li[id^='anchorBoxId_']",
            "title": ".description .name span:nth-child(2)",
            "price": [
                ".description ul.spec li[rel='판매가'] span:nth-child(2)",
                ".description ul.spec li[rel='판매가'] span",
            ],
            "url": ".thumbnail a",
            "image": ".thumbnail a img",
            "sold_out": "img[alt='품절']",
            "page_param": "page",
        }
        return self.get_products_by_selectors(selectors)
