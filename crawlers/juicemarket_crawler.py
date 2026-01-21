"""
액상마켓(juicemarket.kr) 크롤러 구현.
"""
from .base_crawler import BaseCrawler


class JuicemarketCrawler(BaseCrawler):
    """
    액상마켓 웹사이트용 크롤러.
    Cafe24 기반 레이아웃을 사용.
    """

    # 카테고리 URL 매핑
    CATEGORIES = {
        "입호흡": "42",
        "폐호흡": "48",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("juicemarket", headless, env_file=env_file)
        self.base_url = "https://juicemarket.kr"
        self.category = category
        self.category_url = f"{self.base_url}/product/list.html?cate_no={self.CATEGORIES.get(category, self.CATEGORIES['입호흡'])}"

    def get_products(self):
        """
        액상마켓에서 제품을 가져옵니다.
        """
        selectors = {
            "list": ".prdList [id^='anchorBoxId_']",
            "title": ".description .name span:nth-child(2)",
            "price": ".description .spec li.product_price span:nth-child(2)",
            "url": "div.thumbnail a",
            "image": "div.thumbnail img",
            "sold_out": "img[alt='품절']"
        }
        return self.get_products_by_selectors(selectors)
