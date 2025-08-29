"""
카리베이프(karivape) 크롤러 구현.
사이트: https://karivape.com/
"""
import time
from selenium.webdriver.common.by import By
from .base_crawler import BaseCrawler


class KarivapeCrawler(BaseCrawler):
    """
    카리베이프 웹사이트용 크롤러.
    Cafe24 기반 레이아웃과 동일한 셀렉터 패턴을 사용.

    카테고리 (페이징 처리 페이지):
      - 입호흡: https://karivape.com/product/list.html?cate_no=354
      - 폐호흡: https://karivape.com/product/list.html?cate_no=361
    페이징 파라미터: page
    """

    CATEGORIES = {
        "입호흡": "https://karivape.com/product/list.html?cate_no=354",
        "폐호흡": "https://karivape.com/product/list.html?cate_no=361",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("karivape", headless, env_file=env_file)
        self.base_url = "https://karivape.com"
        self.category = category
        self.category_url = self.CATEGORIES.get(category, self.CATEGORIES["입호흡"])

    def get_products(self):
        products = []

        # 페이징 처리: page 파라미터를 증가시키며 제품을 수집
        self.logger.info("페이징을 통해 모든 제품을 로드합니다 (파라미터: page)")
        page = 1
        max_pages = 200  # 안전 장치

        while page <= max_pages:
            page_url = f"{self.category_url}&page={page}" if "?" in self.category_url else f"{self.category_url}?page={page}"
            if not self.navigate_to(page_url):
                self.logger.error(f"페이지 이동 실패: {page_url}")
                break

            time.sleep(2)

            product_elements = self.find_elements(By.CSS_SELECTOR, ".xans-product-listnormal .prdList [id^='anchorBoxId_']")
            self.logger.info(f"페이지 {page}: 제품 수 = {len(product_elements)}")

            if not product_elements:
                if page == 1:
                    self.logger.info("제품 요소를 찾을 수 없어 크롤링 종료")
                else:
                    self.logger.info("더 이상 제품이 없어 페이징을 중단합니다")
                break

            for element in product_elements:
                try:
                    # 품절 여부 확인 (품절 이미지 또는 텍스트)
                    try:
                        is_sold_out_element = element.find_element(By.CSS_SELECTOR, "img[alt='품절']")
                        if is_sold_out_element:
                            continue
                    except Exception:
                        pass

                    # 제목
                    try:
                        title_element = element.find_element(By.CSS_SELECTOR, ".description .name span:nth-child(2)")
                        title = title_element.text.strip() if title_element else "N/A"
                    except Exception as e:
                        self.logger.error(f"제품 제목 추출 실패: {str(e)}")
                        title = "N/A"

                    # 가격
                    price_str = "N/A"
                    try:
                        price_element = element.find_element(By.CSS_SELECTOR, ".description ul.spec li[column_name='product_price'] span:nth-child(3)")
                        price_str = price_element.text.strip() if price_element else "N/A"
                    except Exception as e:
                        self.logger.error(f"가격 추출 실패: {str(e)}")
                        price_str = "N/A"

                    price = 0
                    if price_str != "N/A":
                        try:
                            price = int(price_str.replace('원', '').replace(',', '').strip())
                        except ValueError:
                            self.logger.error(f"가격 변환 실패: {price_str}")
                            price = 0

                    # URL
                    try:
                        url_element = element.find_element(By.CSS_SELECTOR, "div.thumbnail a")
                        relative_url = url_element.get_attribute("href") if url_element else "N/A"
                        url = relative_url if relative_url.startswith("http") else f"{self.base_url}/{relative_url.lstrip('/')}"
                    except Exception as e:
                        self.logger.error(f"제품 URL 추출 실패: {str(e)}")
                        url = "N/A"

                    # 이미지
                    try:
                        img_element = element.find_element(By.CSS_SELECTOR, "div.thumbnail a img")
                        img_url = img_element.get_attribute("src") if img_element else "N/A"
                    except Exception as e:
                        self.logger.error(f"이미지 URL 추출 실패: {str(e)}")
                        img_url = ""

                    product_info = {
                        "title": title,
                        "price": price,
                        "url": url,
                        "image_url": img_url,
                        "detail_comment": ""
                    }
                    products.append(product_info)
                    self.logger.debug(f"제품 정보 추가: {title}")
                except Exception as e:
                    self.logger.error(f"제품 정보 추출 중 오류: {str(e)}")

            page += 1

        self.logger.info(f"총 수집된 제품 수: {len(products)}")
        return products

    def crawl(self, keywords=None, categories=None):
        self.logger.info("카리베이프 크롤링 시작")
        results = {}
        if categories is None:
            categories = list(self.CATEGORIES.keys())
            self.logger.info(f"모든 카테고리 크롤링: {categories}")
        for category in categories:
            if category != self.category:
                self.logger.info(f"카테고리 '{category}' 크롤링을 위한 새 인스턴스 생성")
                crawler = KarivapeCrawler(headless=self.headless, category=category, env_file=self.env_file)
                try:
                    category_products = crawler.get_products()
                    results[category] = category_products
                    self.logger.info(f"카테고리 '{category}'에서 {len(category_products)}개 제품 발견")
                finally:
                    crawler.close()
            else:
                self.logger.info(f"카테고리 '{self.category}' 크롤링 중")
                products = self.get_products()
                results[category] = products
                self.logger.info(f"카테고리 '{self.category}'에서 {len(products)}개 제품 발견")
        return results
