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

    카테고리:
      - 입호흡: https://karivape.com/category/%EC%9E%85%ED%98%B8%ED%9D%A1%EC%95%A1%EC%83%81/354/
      - 폐호흡: https://karivape.com/category/%ED%8F%90%ED%98%B8%ED%9D%A1%EC%95%A1%EC%83%81/361/
    무한 스크롤 기반 로딩 (별도 페이지 이동 없음)
    """

    CATEGORIES = {
        "입호흡": "https://karivape.com/category/%EC%9E%85%ED%98%B8%ED%9D%A1%EC%95%A1%EC%83%81/354/",
        "폐호흡": "https://karivape.com/category/%ED%8F%90%ED%98%B8%ED%9D%A1%EC%95%A1%EC%83%81/361/",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("karivape", headless, env_file=env_file)
        self.base_url = "https://karivape.com"
        self.category = category
        self.category_url = self.CATEGORIES.get(category, self.CATEGORIES["입호흡"])

    def get_products(self):
        if not self.navigate_to(self.category_url):
            self.logger.error("카리베이프 카테고리 페이지로 이동 실패")
            return []
        time.sleep(2)
        products = []

        # 무한 스크롤 로딩 처리
        self.logger.info("무한 스크롤을 통해 모든 제품을 로드합니다")
        max_scrolls = 60  # 안전 장치
        stable_rounds_needed = 3  # 제품 수가 증가하지 않는 라운드 수가 이 값을 넘으면 중단
        stable_rounds = 0
        prev_count = 0

        for i in range(max_scrolls):
            # 스크롤 다운
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)

            # 새로 로드된 제품 수 확인
            current_elements = self.find_elements(By.CSS_SELECTOR, ".normalpackage_box .prdList [id^='anchorBoxId_']")
            current_count = len(current_elements)
            self.logger.info(f"스크롤 {i+1}/{max_scrolls} - 현재 제품 수: {current_count}")

            if current_count <= prev_count:
                stable_rounds += 1
            else:
                stable_rounds = 0
                prev_count = current_count

            # 상단으로 소폭 올렸다가 다시 내리기 (로딩 트리거 보조)
            self.driver.execute_script("window.scrollBy(0, -200);")
            time.sleep(0.3)

            if stable_rounds >= stable_rounds_needed:
                self.logger.info("더 이상 새로운 제품이 로드되지 않아 스크롤을 중단합니다")
                break

        # 최종 로드된 제품 요소 수집
        product_elements = self.find_elements(By.CSS_SELECTOR, ".normalpackage_box .prdList [id^='anchorBoxId_']")
        self.logger.info(f"로딩된 전체 제품 수: {len(product_elements)}")
        if not product_elements:
            self.logger.info("제품 요소를 찾을 수 없어 크롤링 종료")
            return []

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
                    price_element = element.find_element(By.CSS_SELECTOR, ".description ul.spec li:nth-child(2) span:nth-child(2)")
                    price_str = price_element.text.strip() if price_element else "N/A"
                except Exception as e:
                    try:
                        price_element = element.find_element(By.CSS_SELECTOR, ".description ul.spec li:nth-child(1) span:nth-child(2)")
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
