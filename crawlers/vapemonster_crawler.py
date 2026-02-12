"""
베이프몬스터 크롤러 구현.
"""
from .base_crawler import BaseCrawler


class VapeMonsterCrawler(BaseCrawler):
    """
    베이프몬스터 웹사이트용 크롤러.
    """

    # 카테고리 코드 매핑
    CATEGORIES = {
        "입호흡": "/goods/goods_list.php?cateCd=016002",
        "폐호흡": "/goods/goods_list.php?cateCd=016003",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("vapemonster", headless, env_file=env_file)
        self.base_url = "https://www.vapemonster.co.kr"
        self.category = category
        self.category_url = f"{self.base_url}{self.CATEGORIES.get(category, self.CATEGORIES['입호흡'])}"

    def get_products(self):
        """
        베이프몬스터에서 제품을 가져옵니다.
        """
        selectors = {
            "list": "div.item_cont",
            "title": "div.item_tit_box a strong",
            "price": "div.item_money_box strong",
            "url": "div.item_tit_box a",
            "image": "div.item_photo_box img",
            "sold_out": "img[alt='품절']"
        }
        return self.get_products_by_selectors(selectors)
