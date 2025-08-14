"""
haoma111.cafe24.com(베이핑덕) 크롤러 구현.
"""
import time
from selenium.webdriver.common.by import By
from .base_crawler import BaseCrawler

class VapeingduckCrawler(BaseCrawler):
    """
    베이핑덕 웹사이트용 크롤러.
    """
    CATEGORIES = {
        "입호흡": "58",
        "폐호흡": "59",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        super().__init__("vapeingduck", headless, env_file=env_file)
        self.base_url = "https://haoma111.cafe24.com"
        category_path = self.CATEGORIES.get(category, self.CATEGORIES["입호흡"])
        self.category = category
        self.category_path = category_path
        self.category_url = f"{self.base_url}/category/%EC%9E%85%ED%98%B8%ED%9D%A1/{category_path}/" if category == "입호흡" else f"{self.base_url}/category/%ED%8F%90%ED%98%B8%ED%9D%A1/{category_path}/"

    def get_products(self):
        if not self.navigate_to(self.category_url):
            self.logger.error("베이핑덕 카테고리 페이지로 이동 실패")
            return []
        time.sleep(2)
        products = []
        current_page = 1
        has_products = True
        while has_products:
            self.logger.info(f"베이핑덕 {self.category} {current_page}페이지 크롤링 중")
            time.sleep(2)
            product_elements = self.find_elements(By.CSS_SELECTOR, ".prdList li.item")
            if not product_elements:
                self.logger.info("페이지에서 제품 요소를 찾을 수 없음")
                has_products = False
                break
            self.logger.info(f"{current_page}페이지에서 {len(product_elements)}개 제품 발견")
            for element in product_elements:
                try:
                    # 품절 여부 확인
                    try:
                        is_sold_out_element = element.find_element(By.CSS_SELECTOR, "img[alt='품절']")
                        if is_sold_out_element:
                            continue
                    except Exception as e:
                        pass

                    # 제목
                    try:
                        title_element = element.find_element(By.CSS_SELECTOR, ".description .name span:nth-child(2)")
                        title = title_element.text.strip() if title_element else "N/A"
                    except Exception as e:
                        self.logger.error(f"제품 제목 추출 실패: {str(e)}")
                        title = "N/A"
                    # 가격
                    try:
                        price_element = element.find_element(By.CSS_SELECTOR, ".description ul.spec li[rel='판매가'] span:nth-child(2)")
                        price_str = price_element.text.strip() if price_element else "N/A"
                    except Exception as e:
                        self.logger.error(f"가격 추출 실패: {str(e)}")
                        price_str = "N/A"
                    price = 0
                    if price_str != "N/A":
                        try:
                            price = int(price_str.replace('원', '').replace(',', ''))
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

                    product_info = {
                        "title": title,
                        "price": price,
                        "url": url,
                        "image_url": "",
                        "detail_comment": ""
                    }
                    products.append(product_info)
                    self.logger.debug(f"제품 정보 추가: {title}")
                except Exception as e:
                    self.logger.error(f"제품 정보 추출 중 오류: {str(e)}")
            # 다음 페이지 이동
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
        self.logger.info("베이핑덕 크롤링 시작")
        results = {}
        if categories is None:
            categories = list(self.CATEGORIES.keys())
            self.logger.info(f"모든 카테고리 크롤링: {categories}")
        for category in categories:
            if category != self.category:
                self.logger.info(f"카테고리 '{category}' 크롤링을 위한 새 인스턴스 생성")
                crawler = VapeingduckCrawler(headless=self.headless, category=category, env_file=self.env_file)
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