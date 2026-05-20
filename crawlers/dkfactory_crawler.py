"""
DK팩토리(dkfactory) 크롤러 구현.
사이트: https://dkfactory.co.kr/
"""
from .base_crawler import BaseCrawler


class DkFactoryCrawler(BaseCrawler):
    """
    DK팩토리 웹사이트용 크롤러.
    Cafe24 기반 레이아웃을 사용.
    """
    CATEGORIES = {
        "입호흡": "/product/list.html?cate_no=713",
        "폐호흡": "/product/list.html?cate_no=714",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("dkfactory", headless, env_file=env_file)
        self.base_url = "https://dkfactory.co.kr"
        self.category = category
        self.category_url = f"{self.base_url}{self.CATEGORIES.get(category, self.CATEGORIES['입호흡'])}"

    def get_products(self):
        """
        DK팩토리에서 제품을 가져옵니다.
        """
        selectors = {
            "list": ".prdList > li",
            "title": ".description .name a span",
            "price": ".prd-price .sale-price",
            "url": ".description .name a",
            "image": ".thumbnail img",
            "sold_out": "img[src*='icon_pro_soldout']", # 필요 시 조정
            "page_param": "page"
        }
        return self.get_products_by_selectors(selectors)
