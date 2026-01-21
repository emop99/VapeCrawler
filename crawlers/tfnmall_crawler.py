"""
티에프몰(tfnmall) 크롤러 구현.
사이트: https://tfnmall.com/
"""
from .base_crawler import BaseCrawler


class TfnmallCrawler(BaseCrawler):
    """
    티에프몰 웹사이트용 크롤러.
    Cafe24 기반 레이아웃과 동일한 셀렉터 패턴을 사용.
    """

    CATEGORIES = {
        "입호흡": "44",
        "폐호흡": "45",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("tfnmall", headless, env_file=env_file)
        self.base_url = "https://tfnmall.com"
        self.category = category
        # 카테고리 URL 설정
        category_no = self.CATEGORIES.get(category, self.CATEGORIES["입호흡"])
        self.category_url = f"{self.base_url}/product/list.html?cate_no={category_no}"

    def parse_price(self, price_str):
        """티에프몰 특유의 'data-price' 형식(^구분자)을 처리합니다."""
        if price_str and '^' in price_str:
            price_str = price_str.split('^')[1]
        return super().parse_price(price_str)

    def get_products(self):
        """
        티에프몰에서 제품을 가져옵니다.
        """
        selectors = {
            "list": ".xans-product-listnormal .prdList [id^='anchorBoxId_']",
            "title": ".description p.name a span:nth-child(2)",
            "price": {"selector": "", "attribute": "data-price"},
            "url": "div.thumbnail a",
            "image": "div.thumbnail a .add_thumb img",
            "sold_out": "img[alt='품절']"
        }
        return self.get_products_by_selectors(selectors)
