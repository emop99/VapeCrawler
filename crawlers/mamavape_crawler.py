"""
마마베이프(mamavape) 크롤러 구현.
사이트: https://mamavape.co.kr/
"""
from .base_crawler import BaseCrawler


class MamavapeCrawler(BaseCrawler):
    """
    마마베이프 웹사이트용 크롤러.
    Cafe24 기반 레이아웃과 동일한 셀렉터 패턴을 사용.
    """

    CATEGORIES = {
        "입호흡": "https://mamavape.co.kr/category/%EC%9E%85%ED%98%B8%ED%9D%A1%EC%95%A1%EC%83%81/73/",
        "폐호흡": "https://mamavape.co.kr/category/%ED%8F%90%ED%98%B8%ED%9D%A1%EC%95%A1%EC%83%81/74/",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("mamavape", headless, env_file=env_file)
        self.base_url = "https://mamavape.co.kr"
        self.category = category
        self.category_url = self.CATEGORIES.get(category, self.CATEGORIES["입호흡"])

    def get_products(self):
        """
        마마베이프에서 제품을 가져옵니다.
        """
        selectors = {
            "list": ".prdList [id^='anchorBoxId_']",
            "title": ".description .name",
            "price": [
                ".description ul.spec li:nth-child(2) span:nth-child(2)",
                ".description ul.spec li:nth-child(1) span:nth-child(2)"
            ],
            "url": "div.thumbnail a",
            "image": "div.thumbnail a[name^='anchorBoxName_'] img",
            "sold_out": "img[alt='품절']"
        }
        return self.get_products_by_selectors(selectors)
