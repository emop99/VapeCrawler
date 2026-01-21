"""
이삼액상(23juice) 크롤러 구현.
사이트: https://23juice.kr/
"""
from .base_crawler import BaseCrawler


class Juice23Crawler(BaseCrawler):
    """
    이삼액상(23juice) 웹사이트용 크롤러.
    Cafe24 기반 레이아웃과 동일한 셀렉터 패턴을 사용.

    카테고리:
      - 입호흡: https://23juice.kr/product/list.html?cate_no=23
      - 폐호흡: https://23juice.kr/product/list.html?cate_no=43
    페이징: page 파라미터 사용
    """

    CATEGORIES = {
        "입호흡": "https://23juice.kr/product/list.html?cate_no=23",
        "폐호흡": "https://23juice.kr/product/list.html?cate_no=43",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("23juice", headless, env_file=env_file)
        self.base_url = "https://23juice.kr"
        self.category = category
        self.category_url = self.CATEGORIES.get(category, self.CATEGORIES["입호흡"])

    def get_products(self):
        selectors = {
            "list": ".prdList [id^='anchorBoxId_']",
            "title": ".description .name span:nth-child(2)",
            "price": [
                ".description ul.spec li:nth-child(2) span:nth-child(1)",
                ".description ul.spec li:nth-child(1) span:nth-child(1)"
            ],
            "url": "div.thumbnail a",
            "image": "div.add_thumb img",
            "sold_out": "img[alt='품절']"
        }
        products = self.get_products_by_selectors(selectors)
        # '없는액상 톡톡문의' 필터링 추가
        return [p for p in products if p['title'] != '없는액상 톡톡문의']

