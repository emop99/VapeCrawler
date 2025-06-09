"""
99주스 크롤러 구현.
"""
import time
from selenium.webdriver.common.by import By
from .base_crawler import BaseCrawler


class Juice99Crawler(BaseCrawler):
    """
    99주스 웹사이트용 크롤러.
    """

    # 카테고리 URL 매핑
    CATEGORIES = {
        "입호흡": "%EC%9E%85%ED%98%B8%ED%9D%A1-%EC%95%A1%EC%83%81/42",
        "폐호흡": "%ED%8F%90%ED%98%B8%ED%9D%A1-%EC%95%A1%EC%83%81/43",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        """
        99주스 크롤러를 초기화합니다.

        Args:
            headless (bool): 크롬을 헤드리스 모드로 실행할지 여부
            category (str): 크롤링할 카테고리 (입호흡, 폐호흡)
            env_file (str): 환경 변수 파일 경로
        """
        super().__init__("juice99", headless, env_file=env_file)
        self.base_url = "https://99juice.co.kr"

        # 카테고리 URL 경로 가져오기 (없으면 기본값 사용)
        category_path = self.CATEGORIES.get(category, self.CATEGORIES["입호흡"])
        self.category = category
        self.category_path = category_path
        self.category_url = f"{self.base_url}/category/{category_path}/"

    def get_products(self):
        """
        99주스에서 제품을 가져옵니다.
        페이지 파라미터 값을 +1씩 증가시키면서 상품 정보가 있는 한 계속 크롤링합니다.

        Returns:
            list: 제품 정보 딕셔너리 목록
        """
        if not self.navigate_to(self.category_url):
            self.logger.error("99주스 카테고리 페이지로 이동하지 못했습니다")
            return []

        # 페이지가 로드될 때까지 대기
        time.sleep(2)

        products = []
        current_page = 1
        has_products = True

        while has_products:
            self.logger.info(f"99주스 {self.category} 카테고리의 {current_page} 페이지 크롤링 중")

            # 제품 요소가 로드될 때까지 대기
            time.sleep(2)

            # 모든 제품 요소 찾기
            product_elements = self.find_elements(By.CSS_SELECTOR, ".sp-product-item")

            if not product_elements:
                self.logger.info("페이지에서 제품 요소를 찾을 수 없습니다")
                has_products = False
                break

            self.logger.info(f"{current_page} 페이지에서 {len(product_elements)}개의 제품을 찾았습니다")

            # 제품 정보 추출
            for element in product_elements:
                try:
                    # 제품 이미지 URL 추출 (.sp-product-item-thumb img src)
                    img_element = element.find_element(By.CSS_SELECTOR, ".sp-product-item-thumb img")
                    img_url = img_element.get_attribute("src") if img_element else "N/A"

                    # 제품 URL 추출 (.sp-product-item-thumb a href)
                    url_element = element.find_element(By.CSS_SELECTOR, ".sp-product-item-thumb a")
                    url = url_element.get_attribute("href") if url_element else "N/A"

                    # 제품 제목 추출 (.sp-product-name 선택자에 제일 아래 span)
                    try:
                        # .sp-product-name 요소 찾기
                        product_name_element = element.find_element(By.CSS_SELECTOR, ".sp-product-name")
                        # 제일 아래 span 요소 찾기
                        span_elements = product_name_element.find_elements(By.CSS_SELECTOR, "span")
                        if span_elements and len(span_elements) > 0:
                            # 마지막 span 요소의 텍스트 가져오기
                            title_element = span_elements[-1]  # 제일 아래 span
                            title = title_element.text.strip()
                        else:
                            # span이 없으면 전체 텍스트 사용
                            title = product_name_element.text.strip()
                    except Exception as e:
                        self.logger.warning(f"제품 제목 요소를 찾을 수 없습니다: {str(e)}")
                        title = "N/A"

                    # 제품 설명 (없으면 빈 문자열)
                    detail_comment = ""

                    # 제품 가격 추출 (.xans-product-listitem div 셀렉터에 어트리뷰트 rel 값이 할인판매가가 있다면 해당 값을 이용)
                    # 할인판매가가 없다면 판매가 값을 이용하여 추출
                    price = 0
                    try:
                        # 할인판매가 찾기
                        price_elements = element.find_elements(By.CSS_SELECTOR, ".xans-product-listitem div")
                        discount_price_element = None
                        regular_price_element = None

                        for price_element in price_elements:
                            rel_value = price_element.get_attribute("rel")
                            if rel_value == "할인판매가":
                                discount_price_element = price_element
                            elif rel_value == "판매가":
                                regular_price_element = price_element

                        # 할인판매가가 있으면 사용, 없으면 판매가 사용
                        if discount_price_element:
                            # 할인판매가 요소 내의 모든 span 요소 찾기
                            span_elements = discount_price_element.find_elements(By.CSS_SELECTOR, "span")
                            if span_elements and len(span_elements) > 0:
                                # 제일 하단 span 요소의 텍스트 가져오기
                                price_element = span_elements[-1]  # 제일 하단 span
                                price_str = price_element.text.strip()
                            else:
                                # span이 없으면 전체 텍스트 사용
                                price_str = discount_price_element.text.strip()
                        elif regular_price_element:
                            price_str = regular_price_element.text.strip()
                        else:
                            # 대체 선택자 시도
                            price_element = element.find_element(By.CSS_SELECTOR, ".sp-product-item-price")
                            price_str = price_element.text.strip() if price_element else "N/A"
                    except Exception as e:
                        self.logger.warning(f"가격 요소를 찾을 수 없습니다: {str(e)}")
                        price_str = "N/A"

                    # 가격을 정수로 변환 (쉼표 제거, 원 기호 제거)
                    if price_str != "N/A":
                        try:
                            # '원' 제거 및 쉼표 제거 후 정수로 변환
                            price = int(price_str.replace('원', '').replace(',', ''))
                        except ValueError:
                            self.logger.warning(f"가격을 정수로 변환할 수 없습니다: {price_str}")
                            price = 0

                    product_info = {
                        "title": title,
                        "detail_comment": detail_comment,
                        "price": price,
                        "url": url,
                        "image_url": img_url
                    }

                    products.append(product_info)

                except Exception as e:
                    self.logger.error(f"제품 정보 추출 중 오류 발생: {str(e)}")
                    continue

            # 다음 페이지로 이동
            try:
                # 다음 페이지 번호 찾기
                next_page = current_page + 1
                self.logger.info(f"다음 페이지 {next_page}로 이동 시도")

                # 다음 페이지 URL 직접 구성
                try:
                    # 현재 URL에서 페이지 파라미터 변경
                    current_url = self.driver.current_url
                    if "page=" in current_url:
                        next_url = current_url.replace(f"page={current_page}", f"page={next_page}")
                    else:
                        if "?" in current_url:
                            next_url = f"{current_url}&page={next_page}"
                        else:
                            next_url = f"{current_url}?page={next_page}"

                    self.logger.info(f"다음 페이지 URL로 직접 이동: {next_url}")
                    self.navigate_to(next_url)
                    time.sleep(2)  # 페이지가 로드될 때까지 대기
                    current_page = next_page
                    continue
                except Exception as e:
                    self.logger.error(f"다음 페이지 URL 구성 중 오류 발생: {str(e)}")
            except Exception as e:
                self.logger.error(f"다음 페이지로 이동 중 오류 발생: {str(e)}")
                break

        return products

    def crawl(self, keywords=None, categories=None):
        """
        99주스를 위한 주요 크롤링 메서드.

        Args:
            keywords (list): 이 크롤러에서는 사용되지 않음 (카테고리 기반 크롤링)
            categories (list): 크롤링할 카테고리 목록 (입호흡, 폐호흡)

        Returns:
            dict: 카테고리를 제품 목록에 매핑하는 딕셔너리
        """
        self.logger.info("99주스 크롤링 시작")

        results = {}

        # 카테고리가 지정되지 않은 경우 모든 카테고리를 크롤링
        if categories is None:
            all_categories = [cat for cat in self.CATEGORIES.keys()]
            self.logger.info(f"카테고리가 지정되지 않아 모든 카테고리를 크롤링합니다: {all_categories}")
            categories = all_categories

        # 여러 카테고리 크롤링
        for category in categories:
            # 현재 카테고리와 다른 경우에만 새 인스턴스 생성
            if category != self.category:
                self.logger.info(f"카테고리 '{category}' 크롤링을 위한 새 인스턴스 생성")
                # 같은 headless 설정으로 새 인스턴스 생성
                crawler = Juice99Crawler(headless=self.headless, category=category, env_file=self.env_file)
                try:
                    category_products = crawler.get_products()
                    results[category] = category_products
                    product_count = len(category_products)
                    self.logger.info(f"카테고리 '{category}'에서 {product_count}개의 제품을 찾았습니다")
                    if product_count == 0:
                        self.logger.warning(f"카테고리 '{category}'에서 제품을 찾지 못했습니다.")
                finally:
                    # 리소스 정리
                    crawler.close()
            else:
                # 현재 인스턴스로 크롤링
                self.logger.info(f"카테고리 '{self.category}' (경로: {self.category_path}) 크롤링 중")
                products = self.get_products()
                results[category] = products
                self.logger.info(f"카테고리 '{self.category}'에서 {len(products)}개의 제품을 찾았습니다")

        return results
