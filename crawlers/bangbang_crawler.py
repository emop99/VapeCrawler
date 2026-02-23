"""
방방액상(bangbang) 크롤러 구현.
사이트: https://xn--vh3ba246akzf.kr/
"""
from .base_crawler import BaseCrawler


class BangBangCrawler(BaseCrawler):
    """
    방방액상 웹사이트용 크롤러.
    """

    CATEGORIES = {
        "입호흡": "https://xn--vh3ba246akzf.kr/product/list.html?cate_no=43",
        "폐호흡": "https://xn--vh3ba246akzf.kr/product/list.html?cate_no=44",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("bangbang", headless, env_file=env_file)
        self.base_url = "https://xn--vh3ba246akzf.kr"
        self.category = category
        self.category_url = self.CATEGORIES.get(category, self.CATEGORIES["입호흡"])

    def get_products(self):
        """
        방방액상에서 제품을 가져옵니다.
        """
        selectors = {
            "list": "li.df-prl__item",
            "title": ".df-prl__name span",
            "price": {"selector": ".product_price > span", "remove": [".df-discountrate"]},
            "url": "a.df-prl__thumb-link",
            "image": "img.df-prl__thumb-image",
            "sold_out": ".df-prl__icon img[alt='품절']",
            "page_param": "page"
        }
        products = self.get_products_by_selectors(selectors)

        # 상품명에서 [입호흡], [폐호흡] 문구 제거
        for product in products:
            product['title'] = product['title'].replace('[입호흡]', '').replace('[폐호흡]', '').strip()

        return products
