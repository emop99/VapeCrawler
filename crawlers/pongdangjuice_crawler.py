"""
퐁당쥬스 크롤러 구현.
"""
from .base_crawler import BaseCrawler


class PongdangJuiceCrawler(BaseCrawler):
    """
    퐁당쥬스 웹사이트용 크롤러.
    """

    # 카테고리 URL 매핑
    CATEGORIES = {
        "입호흡": "/category/%EC%9E%85%ED%98%B8%ED%9D%A1-30ml/23/",
        "폐호흡": "/category/%ED%8F%90%ED%98%B8%ED%9D%A1-60ml/24/",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("pongdangjuice", headless, env_file=env_file)
        self.base_url = "https://xn--ok1b401a16etxl.com"
        self.category = category
        self.category_url = f"{self.base_url}{self.CATEGORIES.get(category, self.CATEGORIES['입호흡'])}"

    def get_products(self):
        """
        퐁당쥬스에서 제품을 가져옵니다.
        """
        # Cafe24 기반 쇼핑몰의 일반적인 구조에 맞춘 셀렉터
        selectors = {
            "list": ".xans-product-listnormal .prdList [id^='anchorBoxId_']",
            "title": ".description .name:not(.title)",
            "price": ".spec .xans-record-:last-child",
            "url": ".thumbnail a",
            "image": ".thumbnail img",
            "sold_out": "img[alt='품절']",
            "page_param": "page"
        }
        
        # 퐁당쥬스 HTML 특성에 따른 가격 셀렉터 조정
        # .description의 ec-data-price 속성이 있으면 더 정확함
        products = self.get_products_by_selectors(selectors)
        
        # 제목 정규화 로직
        for p in products:
            p['title'] = p['title'].replace("퐁당쥬스", "").replace("입호흡", "").replace("폐호흡", "").replace("액상", "").strip()
        
        return products
