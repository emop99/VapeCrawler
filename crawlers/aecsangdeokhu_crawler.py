"""
액상덕후(aecsangdeokhu) 크롤러 구현.
사이트: https://xn--bn1bn8wqrd0yw.com/
"""
from .base_crawler import BaseCrawler


class AecsangdeokhuCrawler(BaseCrawler):
    """
    액상덕후 웹사이트용 크롤러.
    """

    CATEGORIES = {
        "입호흡": "https://xn--bn1bn8wqrd0yw.com/55",
        "폐호흡": "https://xn--bn1bn8wqrd0yw.com/59",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("aecsangdeokhu", headless, env_file=env_file)
        self.base_url = "https://xn--bn1bn8wqrd0yw.com"
        self.category = category
        self.category_url = self.CATEGORIES.get(category, self.CATEGORIES["입호흡"])

    def get_products(self):
        """
        액상덕후에서 제품을 가져옵니다.
        """
        selectors = {
            "list": "._item_container ._item_wrap .shop-item",
            "title": ".item-detail .shop-title",
            "price": ".item-detail .item-pay-detail .pay",
            "url": "a.shop-item-thumb",
            "image": "a.shop-item-thumb img",
            "sold_out": ".sold_out",
            "last_page": ".paging-block .pagination li a.disabled i.icon-arrow-right"
        }
        return self.get_products_by_selectors(selectors)
