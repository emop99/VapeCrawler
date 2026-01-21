"""
쥬스그램 크롤러 구현.
"""
from .base_crawler import BaseCrawler


class JuicegramCrawler(BaseCrawler):
    """
    쥬스그램 웹사이트용 크롤러.
    """

    # 카테고리 URL 매핑
    CATEGORIES = {
        "입호흡": "28",
        "폐호흡": "26",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        """
        쥬스그램 크롤러를 초기화합니다.

        Args:
            headless (bool): 크롬을 헤드리스 모드로 실행할지 여부
            category (str): 크롤링할 카테고리 (입호흡, 폐호흡)
            env_file (str): 환경 변수 파일 경로
        """
        super().__init__("juicegram", headless, env_file=env_file)
        self.base_url = "https://juicegram.kr"

        # 카테고리 URL 경로 가져오기 (없으면 기본값 사용)
        category_path = self.CATEGORIES.get(category, self.CATEGORIES["입호흡"])
        self.category = category
        self.category_path = category_path
        self.category_url = f"{self.base_url}/product/list.html?cate_no={category_path}"

    def get_products(self):
        """
        쥬스그램에서 제품을 가져옵니다.
        """
        selectors = {
            "list": ".sp-product-box .sp-product-item",
            "title": ".sp-product-name",
            "price": ".sp-product-description div[rel='판매가']",
            "url": ".sp-product-name a",
            "sold_out": "img[alt='품절']"
        }
        return self.get_products_by_selectors(selectors)
