"""
베이프365(vape365) 크롤러 구현.
사이트: https://vape365.kr/
"""
from .base_crawler import BaseCrawler


class Vape365Crawler(BaseCrawler):
    """
    베이프365 웹사이트용 크롤러.
    Cafe24 기반 레이아웃과 동일한 셀렉터 패턴을 사용.
    """

    CATEGORIES = {
        "입호흡": "https://vape365.kr/product/list.html?cate_no=101",
        # "입호흡": "https://vape365.kr/product/list.html?cate_no=60",
        # "폐호흡": "https://vape365.kr/product/list.html?cate_no=61",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("vape365", headless, env_file=env_file)
        self.base_url = "https://vape365.kr"
        self.category = category
        self.category_url = self.CATEGORIES.get(category, self.CATEGORIES["입호흡"])

    def get_products(self):
        """
        베이프365에서 제품을 가져옵니다.
        """
        selectors = {
            "list": ".prdList [id^='anchorBoxId_']",
            "title": ".description .name span:nth-child(2)",
            "price": ".description ul.spec li[rel='판매가'] span:nth-child(2)",
            "url": "div.thumbnail a",
            "image": "div.add_thumb img",
            "sold_out": "img[alt='품절']"
        }
        return self.get_products_by_selectors(selectors)
