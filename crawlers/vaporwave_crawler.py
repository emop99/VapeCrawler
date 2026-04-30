"""
베이퍼웨이브(vaporwave) 크롤러 구현.
사이트: https://vaporwave.co.kr/
"""
from .base_crawler import BaseCrawler


class VaporwaveCrawler(BaseCrawler):
    """
    베이퍼웨이브 웹사이트용 크롤러.
    Cafe24 기반 레이아웃과 동일한 셀렉터 패턴을 사용.
    """
    CATEGORIES = {
        "입호흡": "/products?cate_no=45",
        "폐호흡": "/products?cate_no=44",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("vaporwave", headless, env_file=env_file)
        self.base_url = "https://vaporwave.co.kr"
        self.category = category
        self.category_url = f"{self.base_url}{self.CATEGORIES.get(category, self.CATEGORIES['입호흡'])}"

    def get_products(self):
        """
        베이퍼웨이브에서 제품을 가져옵니다.
        """
        selectors = {
            "list": ".prdList [id^='anchorBoxId_']",
            "title": "div.description > strong > a",
            "price": "div.description > ul > li > span",
            "url": "div.thumbnail a",
            "image": "div.thumbnail a img.img_small",
            "sold_out": "img[src='/cafe24-icons/ico_product_soldout.gif']"
        }
        return self.get_products_by_selectors(selectors)
