"""
주스24 크롤러 구현.
"""
from .base_crawler import BaseCrawler


class Juice24Crawler(BaseCrawler):
    """
    주스24 웹사이트용 크롤러.
    """

    # 카테고리 URL 매핑
    CATEGORIES = {
        "입호흡": "48",
        "폐호흡": "49",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("juice24", headless, env_file=env_file)
        self.base_url = "https://juice24.kr"
        self.category = category
        self.category_url = f"{self.base_url}/product/list.html?cate_no={self.CATEGORIES.get(category, self.CATEGORIES['입호흡'])}"

    def get_products(self):
        """
        주스24에서 제품을 가져옵니다.
        """
        selectors = {
            "list": "ul.prdList li.swiper-slide.xans-record-",
            "title": ".description .name",
            "price": ".description li.msale span.m_item",
            "url": ".thumbnail .prdImg a",
            "image": ".thumbnail .prdImg img",
            "sold_out": "div.soldout:not(.displaynone)"
        }
        return self.get_products_by_selectors(selectors)
