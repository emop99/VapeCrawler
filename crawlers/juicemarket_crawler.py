"""
액상마켓(juicemarket.kr) 크롤러 구현.
"""
import time
import re
from selenium.webdriver.common.by import By
from .base_crawler import BaseCrawler


class JuicemarketCrawler(BaseCrawler):
    """
    액상마켓 웹사이트용 크롤러.
    Cafe24 기반 레이아웃을 사용.
    """

    # 카테고리 URL 매핑
    CATEGORIES = {
        "입호흡": "42",
        "폐호흡": "48",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        """
        액상마켓 크롤러를 초기화합니다.

        Args:
            headless (bool): 크롬을 헤드리스 모드로 실행할지 여부
            category (str): 크롤링할 카테고리 (입호흡, 폐호흡)
            env_file (str): 환경 변수 파일 경로
        """
        super().__init__("juicemarket", headless, env_file=env_file)
        self.base_url = "https://juicemarket.kr"

        # 카테고리 URL 경로 가져오기 (없으면 기본값 사용)
        cate_no = self.CATEGORIES.get(category, self.CATEGORIES["입호흡"])
        self.category = category
        self.category_url = f"{self.base_url}/product/list.html?cate_no={cate_no}"

    def get_products(self):
        """
        액상마켓에서 제품을 가져옵니다.
        페이지 파라미터 값을 +1씩 증가시키면서 상품 정보가 있는 한 계속 크롤링합니다.

        Returns:
            list: 제품 정보 딕셔너리 목록
        """
        if not self.navigate_to(self.category_url):
            self.logger.error("액상마켓 카테고리 페이지로 이동하지 못했습니다")
            return []

        # 페이지가 로드될 때까지 대기
        time.sleep(2)

        products = []
        current_page = 1
        has_products = True

        while has_products:
            self.logger.info(f"액상마켓 {self.category} 카테고리의 {current_page} 페이지 크롤링 중")

            # 제품 요소가 로드될 때까지 대기
            time.sleep(2)

            # Cafe24 일반적인 제품 목록 선택자
            product_elements = self.find_elements(By.CSS_SELECTOR, ".prdList [id^='anchorBoxId_']")

            if not product_elements:
                self.logger.info("페이지에서 제품 요소를 찾을 수 없습니다.")
                has_products = False
                break

            self.logger.info(f"{current_page} 페이지에서 {len(product_elements)}개의 제품을 찾았습니다")

            page_added_count = 0
            # 제품 정보 추출
            for element in product_elements:
                try:
                    # 품절 여부 확인
                    try:
                        is_sold_out_element = element.find_element(By.CSS_SELECTOR, "img[alt='품절']")
                        if is_sold_out_element:
                            continue
                    except Exception as e:
                        pass

                    # 제품 제목 추출
                    try:
                        title_element = element.find_element(By.CSS_SELECTOR, ".description .name span:nth-child(2)")
                        title = title_element.text.strip() if title_element else "N/A"
                    except Exception as e:
                        self.logger.error(f"제품 제목 요소를 찾을 수 없습니다: {str(e)}")
                        title = "N/A"

                    # 제품 설명 추출
                    detail_comment = ""

                    # 제품 가격 추출
                    try:
                        price_element = element.find_element(By.CSS_SELECTOR, ".description .spec li.product_price span:nth-child(2)")
                        price_str = price_element.text.strip() if price_element else "N/A"
                    except Exception as e:
                        self.logger.error(f"가격 요소를 찾을 수 없습니다: {str(e)}")
                        price_str = "N/A"

                    # 가격을 정수로 변환 (쉼표 제거, 원 기호 제거)
                    price = 0
                    if price_str != "N/A":
                        try:
                            # '원' 제거 및 쉼표 제거 후 정수로 변환
                            price = int(price_str.replace('원', '').replace(',', ''))
                        except ValueError:
                            self.logger.error(f"가격을 정수로 변환할 수 없습니다: {price_str}")
                            price = 0

                    # 제품 URL 추출
                    try:
                        url_element = element.find_element(By.CSS_SELECTOR, "div.thumbnail a")
                        relative_url = url_element.get_attribute("href") if url_element else "N/A"
                        url = relative_url if relative_url.startswith("http") else f"{self.base_url}/{relative_url.lstrip('/')}"
                    except Exception as e:
                        self.logger.error(f"제품 URL 요소를 찾을 수 없습니다: {str(e)}")
                        url = "N/A"

                    # 제품 이미지 URL 추출
                    try:
                        img_element = element.find_element(By.CSS_SELECTOR, "div.thumbnail img")
                        img_url = img_element.get_attribute("src") if img_element else ""
                    except Exception as e:
                        self.logger.warning(f"제품 이미지 URL 요소를 찾을 수 없습니다: {str(e)}")
                        img_url = ""

                    # 제품 정보를 딕셔너리로 생성하여 products 배열에 추가
                    product_info = {
                        "title": title,
                        "detail_comment": detail_comment,
                        "price": price,
                        "url": url,
                        "image_url": img_url
                    }

                    products.append(product_info)
                    page_added_count += 1
                except Exception as e:
                    self.logger.error(f"제품 정보 추출 중 오류 발생: {str(e)}")
                    continue

            if page_added_count == 0:
                self.logger.info("현재 페이지에서 추가된 제품이 없습니다. 크롤링을 종료합니다.")
                break

            # 다음 페이지로 이동
            try:
                next_page = current_page + 1
                current_url = self.driver.current_url
                
                if "page=" in current_url:
                    next_url = re.sub(r'page=\d+', f'page={next_page}', current_url)
                else:
                    connector = "&" if "?" in current_url else "?"
                    next_url = f"{current_url}{connector}page={next_page}"

                self.logger.info(f"다음 페이지 {next_page}로 이동 시도: {next_url}")
                self.navigate_to(next_url)
                time.sleep(2)
                
                # 페이지 이동 후 실제 데이터가 있는지 확인하는 로직 (Cafe24는 빈 페이지가 나올 수 있음)
                new_products = self.find_elements(By.CSS_SELECTOR, "ul.prdList > li")
                if not new_products:
                    self.logger.info("다음 페이지에 제품이 없습니다. 크롤링을 종료합니다.")
                    break
                    
                current_page = next_page
            except Exception as e:
                self.logger.error(f"다음 페이지 이동 중 오류 발생: {str(e)}")
                break

        return products

    def crawl(self, keywords=None, categories=None):
        """
        액상마켓을 위한 주요 크롤링 메서드.

        Args:
            keywords (list): 검색 키워드 (카테고리 기반이므로 기본적으로 무시됨)
            categories (list): 크롤링할 카테고리 목록 (입호흡, 폐호흡)

        Returns:
            dict: 카테고리를 제품 목록에 매핑하는 딕셔너리
        """
        self.logger.info("액상마켓 크롤링 시작")

        results = {}

        if categories is None:
            categories = list(self.CATEGORIES.keys())

        for category in categories:
            if category != self.category:
                crawler = JuicemarketCrawler(headless=self.headless, category=category, env_file=self.env_file)
                try:
                    category_products = crawler.get_products()
                    results[category] = category_products
                    self.logger.info(f"카테고리 '{category}'에서 {len(category_products)}개의 제품을 찾았습니다")
                finally:
                    crawler.close()
            else:
                products = self.get_products()
                results[category] = products
                self.logger.info(f"카테고리 '{self.category}'에서 {len(products)}개의 제품을 찾았습니다")

        return results
