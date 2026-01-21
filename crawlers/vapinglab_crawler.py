"""
베이핑랩 크롤러 구현.
"""
from .base_crawler import BaseCrawler


class VapingLabCrawler(BaseCrawler):
    """
    베이핑랩 웹사이트용 크롤러.
    """

    # 카테고리 URL 매핑
    CATEGORIES = {
        "입호흡": "https://vapinglab.co.kr/untitled-5",
        "폐호흡": "https://vapinglab.co.kr/untitled-4",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("vapinglab", headless, env_file=env_file)
        self.base_url = "https://vapinglab.co.kr"
        self.category = category
        self.category_url = self.CATEGORIES.get(category, self.CATEGORIES["입호흡"])

    def get_products(self):
        """
        베이핑랩에서 제품을 가져옵니다.
        """
        selectors = {
            "list": ".shopProductWrapper",
            "title": ".shopProductNameAndPriceDiv .productName",
            "price": ".shopProductNameAndPriceDiv .price span",
            "url": "a",
            "image": {"selector": ".thumbDiv .img", "attribute": "imgsrc"},
            "sold_out": ".soldOutBadge",
            "next_url_template": "{category_url}?productListFilter=allFilter&productListPage={page}&productSortFilter=PRODUCT_ORDER_NO"
        }
        return self.get_products_by_selectors(selectors)
