"""
주스박스 크롤러 구현.
"""
from .base_crawler import BaseCrawler


class JuiceboxCrawler(BaseCrawler):
    """
    주스박스 웹사이트용 크롤러.
    """

    # 카테고리 URL 매핑
    CATEGORIES = {
        "입호흡": "52",
        "폐호흡": "51",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("juicebox", headless, env_file=env_file)
        self.base_url = "https://juicebox.co.kr"
        self.category = category
        self.category_url = f"{self.base_url}/product/list.html?cate_no={self.CATEGORIES.get(category, self.CATEGORIES['입호흡'])}"

    def get_products(self):
        """
        주스박스에서 제품을 가져옵니다.
        """
        selectors = {
            "list": ".prdList__item",
            "title": ".description .name a",
            "price": ".description .spec_wrap .product_price span:nth-child(2)",
            "url": ".description .name a",
            "sold_out": "img[alt='품절']"
        }
        products = self.get_products_by_selectors(selectors)
        
        # 제목 정규화 로직 적용 (기존 코드 유지)
        for p in products:
            p['title'] = p['title'].replace("juicebox", "").replace("JUICE BOX", "").strip()
            
        return products
