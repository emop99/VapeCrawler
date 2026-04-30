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
        "입호흡": "/categories/liquid-mtl",
        "폐호흡": "/categories/liquid-dtl",
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
            "list": "body > div.min-h-screen.flex.flex-col.w-full > main > div > div.grid.grid-cols-2.md\\:grid-cols-4.lg\:grid-cols-5.gap-x-3.gap-y-6 > a",
            "title": "div.px-0\\.5 > h3",
            "price": "div.px-0\\.5 > div.mb-1 > span.text-\\[14px\\].sm\\:text-\\[15px\\].font-bold.text-\\[\\#111\\]",
            "url": "",
            "image": "div.relative.bg-white.overflow-hidden.mb-2.border.border-\\[\\#f0f0f0\\].rounded > div.aspect-square.flex.items-center.justify-center > img",
            "sold_out": "div.px-0\\.5 > div.flex.gap-0\\.5.flex-wrap > span"
        }
        return self.get_products_by_selectors(selectors)
