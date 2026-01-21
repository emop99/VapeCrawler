"""
마녀쥬스(witchjuice) 크롤러 구현.
사이트: https://witchjuice.kr/
"""
from .base_crawler import BaseCrawler


class WitchjuiceCrawler(BaseCrawler):
    """
    마녀쥬스 웹사이트용 크롤러.
    """

    CATEGORIES = {
        "입호흡": "https://witchjuice.kr/category/30ml/42/",
        "폐호흡": "https://witchjuice.kr/category/100ml/43/",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("witchjuice", headless, env_file=env_file)
        self.base_url = "https://witchjuice.kr"
        self.category = category
        self.category_url = self.CATEGORIES.get(category, self.CATEGORIES["입호흡"])

    def get_products(self):
        """
        마녀쥬스에서 제품을 가져옵니다.
        """
        selectors = {
            "list": ".prdList [id^='anchorBoxId_']",
            "title": ".description .name span:nth-child(2)",
            "price": ".description ul.spec li span:nth-child(2)",
            "url": "div.thumbnail a",
            "image": "div.thumbnail a img",
            "sold_out": "img[alt='품절']"
        }
        return self.get_products_by_selectors(selectors)
