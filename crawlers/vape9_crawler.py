"""
vape9.co.kr(베이프나인) 크롤러 구현.
"""
from .base_crawler import BaseCrawler

class Vape9Crawler(BaseCrawler):
    """
    베이프나인 웹사이트용 크롤러.
    """
    CATEGORIES = {
        "입호흡": "25",
        "폐호흡": "74",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("vape9", headless, env_file=env_file)
        self.base_url = "https://vape9.co.kr"
        self.category = category
        self.category_url = f"{self.base_url}/product/list.html?cate_no={self.CATEGORIES.get(category, self.CATEGORIES['입호흡'])}"

    def get_products(self):
        """
        베이프나인에서 제품을 가져옵니다.
        """
        selectors = {
            "list": ".prdList [id^='anchorBoxId_']",
            "title": ".description .name span:nth-child(2)",
            "price": ".description ul.spec li.product_price span:nth-child(3)",
            "url": "div.thumbnail a",
            "image": "div.thumbnail a img",
            "sold_out": "img[alt='품절']"
        }
        products = self.get_products_by_selectors(selectors)
        # '오프라인 전용' 필터링 (기존 로직 유지)
        return [p for p in products if "오프라인 전용" not in p.get('title', '')]

