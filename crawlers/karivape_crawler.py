"""
카리베이프(karivape) 크롤러 구현.
사이트: https://karivape.com/
"""
from .base_crawler import BaseCrawler


class KarivapeCrawler(BaseCrawler):
    """
    카리베이프 웹사이트용 크롤러.
    Cafe24 기반 레이아웃과 동일한 셀렉터 패턴을 사용.

    카테고리 (페이징 처리 페이지):
      - 입호흡: https://karivape.com/product/list.html?cate_no=354
      - 폐호흡: https://karivape.com/product/list.html?cate_no=361
    페이징 파라미터: page
    """

    CATEGORIES = {
        "입호흡": "https://karivape.com/product/list.html?cate_no=354",
        "폐호흡": "https://karivape.com/product/list.html?cate_no=361",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("karivape", headless, env_file=env_file)
        self.base_url = "https://karivape.com"
        self.category = category
        self.category_url = self.CATEGORIES.get(category, self.CATEGORIES["입호흡"])

    def get_products(self):
        """
        카리베이프에서 제품을 가져옵니다.
        """
        selectors = {
            "list": ".xans-product-listnormal .prdList [id^='anchorBoxId_']",
            "title": ".description .name span:nth-child(2)",
            "price": ".description ul.spec li[column_name='product_price'] span:nth-child(3)",
            "url": "div.thumbnail a",
            "image": "div.thumbnail a img",
            "sold_out": "img[alt='품절']"
        }
        return self.get_products_by_selectors(selectors)

