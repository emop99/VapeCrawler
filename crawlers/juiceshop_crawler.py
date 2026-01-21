"""
주스샵 크롤러 구현.
"""
from .base_crawler import BaseCrawler


class JuiceshopCrawler(BaseCrawler):
    """
    주스샵 웹사이트용 크롤러.
    """

    # 카테고리 URL 매핑
    CATEGORIES = {
        "입호흡": "44",
        "폐호흡": "45",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("juiceshop", headless, env_file=env_file)
        self.base_url = "https://juiceshop.kr"
        self.category = category
        self.category_url = f"{self.base_url}/product/list.html?cate_no={self.CATEGORIES.get(category, self.CATEGORIES['입호흡'])}"

    def get_products(self):
        """
        주스샵에서 제품을 가져옵니다.
        """
        selectors = {
            "list": ".prdList .item",
            "title": ".description .name a span:nth-child(2)",
            "price": ".description ul li[rel='판매가'] span:nth-child(2)",
            "url": ".description .name a",
            "image": {"selector": ".thumbnail a img", "attribute": "ec-data-src"},
            "sold_out": "img[alt='품절']"
        }
        return self.get_products_by_selectors(selectors)

