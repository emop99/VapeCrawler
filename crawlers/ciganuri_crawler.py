"""
시가누리(ciganuri) 크롤러 구현.
사이트: https://xn--o39a37i99gz8j.com

Cafe24 기반 사이트와 유사한 리스트 셀렉터를 사용합니다.
카테고리:
  - 입호흡: https://xn--o39a37i99gz8j.com/product/list.html?cate_no=73
  - 폐호흡: https://xn--o39a37i99gz8j.com/product/list.html?cate_no=74
페이징: page 파라미터 사용
"""
import time
from selenium.webdriver.common.by import By
from .base_crawler import BaseCrawler


class CiganuriCrawler(BaseCrawler):
    """
    시가누리 웹사이트용 크롤러.
    Cafe24 기반 레이아웃과 동일한 셀렉터 패턴을 사용.
    """

    CATEGORIES = {
        "입호흡": "https://xn--o39a37i99gz8j.com/product/list.html?cate_no=73",
        "폐호흡": "https://xn--o39a37i99gz8j.com/product/list.html?cate_no=74",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("ciganuri", headless, env_file=env_file)
        self.base_url = "https://xn--o39a37i99gz8j.com"
        self.category = category
        self.category_url = self.CATEGORIES.get(category, self.CATEGORIES["입호흡"])

    def get_products(self):
        if not self.navigate_to(self.category_url):
            self.logger.error("시가누리 카테고리 페이지로 이동 실패")
            return []
        time.sleep(2)
        products = []
        current_page = 1
        while True:
            self.logger.info(f"시가누리 {self.category} {current_page}페이지 크롤링 중")
            time.sleep(2)
            # Cafe24 공통 리스트 셀렉터: 각 상품 앵커 박스 id로 식별
            product_elements = self.find_elements(By.CSS_SELECTOR, ".xans-product-listnormal .prdList [id^='anchorBoxId_']")
            if not product_elements:
                self.logger.info("페이지에서 제품 요소를 찾을 수 없음 — 크롤링 종료")
                break
            self.logger.info(f"{current_page}페이지에서 {len(product_elements)}개 제품 발견")
            for element in product_elements:
                try:
                    # 품절 여부 확인 (품절 배지/텍스트가 있을 경우 스킵)
                    try:
                        soldout_img = element.find_element(By.CSS_SELECTOR, "img[alt='품절']")
                        if soldout_img:
                            continue
                    except Exception:
                        pass

                    # 제목
                    title = "N/A"
                    try:
                        # 기본 Cafe24 테마: .description .name span:nth-child(2)
                        title_element = element.find_element(By.CSS_SELECTOR, ".description .name span:nth-child(2)")
                        title = title_element.text.strip() if title_element else "N/A"
                        if not title or title == "N/A":
                            # 대안: .name > a 또는 .name
                            try:
                                alt_title = element.find_element(By.CSS_SELECTOR, ".description .name a")
                                title = alt_title.text.strip()
                            except Exception:
                                pass
                    except Exception as e:
                        self.logger.warning(f"제품 제목 추출 실패: {str(e)}")

                    # 가격
                    price = 0
                    try:
                        price_element = element.find_element(By.CSS_SELECTOR, ".description ul.spec li[column_name='product_price'] span:nth-child(2)")
                        price_str = price_element.text.strip() if price_element else ""
                        if price_str:
                            try:
                                price = int(price_str.replace('원', '').replace(',', '').strip())
                            except ValueError:
                                self.logger.warning(f"가격 변환 실패: {price_str}")
                    except Exception as e:
                        self.logger.warning(f"가격 추출 실패: {str(e)}")

                    # URL
                    url = "N/A"
                    try:
                        url_element = element.find_element(By.CSS_SELECTOR, "div.thumbnail a")
                        href = url_element.get_attribute("href") if url_element else None
                        if href:
                            url = href if href.startswith("http") else f"{self.base_url}/{href.lstrip('/')}"
                    except Exception as e:
                        self.logger.warning(f"제품 URL 추출 실패: {str(e)}")

                    # 이미지
                    img_url = ""
                    try:
                        img_element = element.find_element(By.CSS_SELECTOR, "div.thumbnail a img")
                        img_url = img_element.get_attribute("src") if img_element else ""
                    except Exception as e:
                        self.logger.warning(f"이미지 URL 추출 실패: {str(e)}")

                    product_info = {
                        "title": title,
                        "price": price,
                        "url": url,
                        "image_url": img_url,
                        "detail_comment": ""
                    }
                    products.append(product_info)
                except Exception as e:
                    self.logger.error(f"제품 정보 추출 중 오류: {str(e)}")

            # 다음 페이지로 이동 (page 파라미터 사용)
            try:
                next_page = current_page + 1
                current_url = self.driver.current_url
                if "page=" in current_url:
                    next_url = current_url.replace(f"page={current_page}", f"page={next_page}")
                else:
                    if "?" in current_url:
                        next_url = f"{current_url}&page={next_page}"
                    else:
                        next_url = f"{current_url}?page={next_page}"
                self.logger.info(f"다음 페이지 이동: {next_url}")
                self.navigate_to(next_url)
                time.sleep(2)
                current_page = next_page
                continue
            except Exception as e:
                self.logger.error(f"다음 페이지 이동 실패: {str(e)}")
                break

        return products

    def crawl(self, keywords=None, categories=None):
        self.logger.info("시가누리 크롤링 시작")
        results = {}
        if categories is None:
            categories = list(self.CATEGORIES.keys())
            self.logger.info(f"모든 카테고리 크롤링: {categories}")
        for category in categories:
            if category != self.category:
                self.logger.info(f"카테고리 '{category}' 크롤링을 위한 새 인스턴스 생성")
                crawler = CiganuriCrawler(headless=self.headless, category=category, env_file=self.env_file)
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
