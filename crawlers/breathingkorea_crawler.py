"""
BreathingKorea 크롤러 구현.
"""
from .base_crawler import BaseCrawler


class BreathingKoreaCrawler(BaseCrawler):
    """
    BreathingKorea 웹사이트용 크롤러.
    """

    # 카테고리 URL 매핑
    CATEGORIES = {
        "입호흡": "60",
        "폐호흡": "43",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("breathingkorea", headless, env_file=env_file)
        self.base_url = "https://xn--9k3b21rv1k.com"
        self.category = category
        self.category_url = f"{self.base_url}/product/list.html?cate_no={self.CATEGORIES.get(category, self.CATEGORIES['입호흡'])}"

    def get_products(self):
        """
        BreathingKorea에서 제품을 가져옵니다.
        """
        selectors = {
            "list": ".prdList [id^='anchorBoxId_']",
            "title": ".description .name span:nth-child(2)",
            "price": ".description ul.spec span:nth-child(2)",
            "url": "div.thumbnail a",
            "image": "div.thumbnail .add_thumb img",
            "sold_out": "img[alt='품절']"
        }
        return self.get_products_by_selectors(selectors)