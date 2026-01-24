"""
일렉샵(elecshop) crawler implementation.
Site: https://elecshop.co.kr/
"""
from .base_crawler import BaseCrawler


class ElecshopCrawler(BaseCrawler):
    """
    일렉샵 site crawler.
    Cafe24 기반 사이트로 일반적인 상품 리스트 셀렉터를 사용.
    """

    CATEGORIES = {
        "입호흡": "https://elecshop.co.kr/product/list.html?cate_no=2567",
        "폐호흡": "https://elecshop.co.kr/product/list.html?cate_no=2569",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("elecshop", headless, env_file=env_file)
        self.base_url = "https://elecshop.co.kr"
        self.category = category
        self.category_url = self.CATEGORIES.get(category, self.CATEGORIES["입호흡"])

    def get_products(self):
        """
        일렉샵에서 상품 정보를 수집합니다.
        """
        selectors = {
            "list": ".xans-product-listnormal .df-wrap-content [id^='anchorBoxId_']",
            "title": ".df-prl__info a",
            "price": [
                {
                    "selector": ".df-prl__info .prd_price_sale span:nth-child(2)",
                    "remove": [".df-discountrate"],
                },
                {
                    "selector": ".product_price span:nth-child(2)",
                    "remove": [".df-discountrate"],
                },
            ],
            "url": ".df-prl__info a",
            "image": ".df-prl__thumb a img",
            "sold_out": "img[alt='품절']",
            "page_param": "page",
        }
        return self.get_products_by_selectors(selectors)
