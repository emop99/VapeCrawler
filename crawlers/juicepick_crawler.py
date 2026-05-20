"""
쥬스픽(juicepick) 크롤러 구현.
사이트: https://juicepick.co.kr/
"""
from .base_crawler import BaseCrawler


class JuicePickCrawler(BaseCrawler):
    """
    쥬스픽 웹사이트용 크롤러.
    Cafe24 기반 레이아웃을 사용.
    """
    CATEGORIES = {
        "입호흡": "/product/list.html?cate_no=216",
        "폐호흡": "/product/list.html?cate_no=204",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("juicepick", headless, env_file=env_file)
        self.base_url = "https://juicepick.co.kr"
        self.category = category
        self.category_url = f"{self.base_url}{self.CATEGORIES.get(category, self.CATEGORIES['입호흡'])}"

    def get_products(self):
        """
        쥬스픽에서 제품을 가져옵니다.
        """
        selectors = {
            "list": ".prdList > li",
            "title": ".description .name a span:nth-child(2)",
            "price": ".product_price span:nth-child(2)",
            "url": ".name > a",
            "image": ".prdImg img",
            "sold_out": "img[alt='품절']", # 기본 Cafe24 패턴, 필요시 조정
            "page_param": "page"
        }
        return self.get_products_by_selectors(selectors)
