"""
49vape 크롤러 구현.
"""
from .base_crawler import BaseCrawler


class Vape49Crawler(BaseCrawler):
    """
    49vape 웹사이트용 크롤러.
    """

    # 카테고리 URL 매핑
    CATEGORIES = {
        "입호흡": "26",
        "폐호흡": "28",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        """
        49vape 크롤러를 초기화합니다.

        Args:
            headless (bool): 크롬을 헤드리스 모드로 실행할지 여부
            category (str): 크롤링할 카테고리 (입호흡, 폐호흡)
            env_file (str): 환경 변수 파일 경로
        """
        super().__init__("vape49", headless, env_file=env_file)
        self.base_url = "https://49vape.com"

        # 카테고리 URL 경로 가져오기 (없으면 기본값 사용)
        category_path = self.CATEGORIES.get(category, self.CATEGORIES["입호흡"])
        self.category = category
        self.category_path = category_path
        self.category_url = f"{self.base_url}/product/list.html?cate_no={category_path}"

    def get_products(self):
        """
        49vape에서 제품을 가져옵니다.
        """
        selectors = {
            "list": ".xans-product-listnormal .prdList [id^='anchorBoxId_']",
            "title": ".description .name span:nth-child(2)",
            "price": ".description ul.spec span:nth-child(2)",
            "url": "div.thumbnail a",
            "sold_out": "img[alt='품절']"
        }
        return self.get_products_by_selectors(selectors)
