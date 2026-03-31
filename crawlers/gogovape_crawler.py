"""
고고액상(gogovape) 크롤러 구현.
"""
from .base_crawler import BaseCrawler


class GogovapeCrawler(BaseCrawler):
    """
    고고액상 웹사이트용 크롤러.
    """

    # 카테고리 URL 매핑
    CATEGORIES = {
        "입호흡": "43",
        "폐호흡": "44",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("gogovape", headless, env_file=env_file)
        self.base_url = "https://gogovape.kr"
        self.category = category
        self.category_url = f"{self.base_url}/product/list.html?cate_no={self.CATEGORIES.get(category, self.CATEGORIES['입호흡'])}"

    def get_products(self):
        """
        고고액상에서 제품을 가져옵니다.
        """
        selectors = {
            "list": ".xans-product-listnormal .prdList [id^='anchorBoxId_']",
            "title": ".description .name:not(.title)",
            "price": ".spec span:has(+ #span_product_tax_type_text)",
            "url": ".thumbnail .prdImg a",
            "image": ".thumbnail .prdImg a img",
            "sold_out": "img[alt='품절']",
            "page_param": "page"
        }
        
        products = self.get_products_by_selectors(selectors)
        
        # 제목 정규화 로직
        for p in products:
            p['title'] = p['title'].replace("고고액상", "").replace("입호흡", "").replace("폐호흡", "").replace("액상", "").replace("[얼려먹구싶오]", "").strip()
        
        return products
