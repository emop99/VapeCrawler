"""
전담액상비비(vapebibi) 크롤러 구현.
사이트: https://xn--jk1bo8sa06werixle.com/
"""
from .base_crawler import BaseCrawler


class VapebibiCrawler(BaseCrawler):
    """
    전담액상비비 웹사이트용 크롤러.
    Cafe24 기반 레이아웃과 동일한 셀렉터 패턴을 사용.
    """
    CATEGORIES = {
        "입호흡": "26",
        "폐호흡": "27",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("vapebibi", headless, env_file=env_file)
        self.base_url = "https://xn--jk1bo8sa06werixle.com"
        self.category = category
        self.category_url = f"{self.base_url}/product/list.html?cate_no={self.CATEGORIES.get(category, self.CATEGORIES['입호흡'])}"

    def get_products(self):
        """
        전담액상비비에서 제품을 가져옵니다.
        """
        selectors = {
            "list": ".prdList [id^='anchorBoxId_']",
            "title": ".description .name span:nth-child(2)",
            "price": ".description ul.spec li.product_price span:nth-child(3)",
            "url": "div.thumbnail a",
            "image": "div.thumbnail a img",
            "sold_out": "img[alt='품절']"
        }
        return self.get_products_by_selectors(selectors)
