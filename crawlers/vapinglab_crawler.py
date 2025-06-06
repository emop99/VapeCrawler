"""
베이핑랩 크롤러 구현.
"""
import time
import re
from selenium.webdriver.common.by import By
from .base_crawler import BaseCrawler


class VapingLabCrawler(BaseCrawler):
    """
    베이핑랩 웹사이트용 크롤러.
    """

    # 카테고리 URL 매핑
    CATEGORIES = {
        "입호흡": "untitled-5",
        "폐호흡": "untitled-4",
    }

    def __init__(self, headless=True, category="입호흡", env_file='.env'):
        """
        베이핑랩 크롤러를 초기화합니다.

        Args:
            headless (bool): 크롬을 헤드리스 모드로 실행할지 여부
            category (str): 크롤링할 카테고리 (입호흡, 폐호흡)
            env_file (str): 환경 변수 파일 경로
        """
        super().__init__("vapinglab", headless, env_file=env_file)
        self.base_url = "https://vapinglab.co.kr"

        # 카테고리 URL 경로 가져오기 (없으면 기본값 사용)
        category_path = self.CATEGORIES.get(category, self.CATEGORIES["입호흡"])
        self.category = category
        self.category_path = category_path
        self.category_url = f"{self.base_url}/{category_path}"

    def get_products(self):
        """
        베이핑랩에서 제품을 가져옵니다.
        페이지 파라미터 값을 +1씩 증가시키면서 상품 정보가 있는 한 계속 크롤링합니다.

        Returns:
            list: 제품 정보 딕셔너리 목록
        """
        if not self.navigate_to(self.category_url):
            self.logger.error("베이핑랩 카테고리 페이지로 이동하지 못했습니다")
            return []

        # 페이지가 로드될 때까지 대기
        time.sleep(2)

        products = []
        current_page = 1
        has_products = True

        while has_products:
            self.logger.info(f"베이핑랩 {self.category} 카테고리의 {current_page} 페이지 크롤링 중")

            # 제품 요소가 로드될 때까지 대기
            time.sleep(2)

            # 모든 제품 요소 찾기 (베이핑랩 사이트 구조에 맞는 선택자)
            # 이슈 설명에서 제공된 HTML 구조에 맞게 선택자 설정
            product_elements = self.find_elements(By.CSS_SELECTOR, ".shopProductWrapper")

            if not product_elements:
                self.logger.warning("페이지에서 제품 요소를 찾을 수 없습니다")
                has_products = False
                break

            self.logger.info(f"{current_page} 페이지에서 {len(product_elements)}개의 제품을 찾았습니다")

            # 제품 정보 추출
            for element in product_elements:
                try:
                    # 제품 제목 추출
                    try:
                        title_element = element.find_element(By.CSS_SELECTOR, ".shopProductNameAndPriceDiv .productName")
                        title = title_element.text.strip() if title_element else "N/A"
                    except Exception as e:
                        self.logger.error(f"제품 제목 요소를 찾을 수 없습니다: {str(e)}")
                        title = "N/A"
                        exit()

                    # 제품 설명 추출
                    detail_comment = ""

                    # 제품 가격 추출 (베이핑랩 사이트 구조에 맞는 선택자)
                    try:
                        price_element = element.find_element(By.CSS_SELECTOR, ".shopProductNameAndPriceDiv .price span")
                        price_str = price_element.text.strip() if price_element else "N/A"
                    except Exception as e:
                        self.logger.error(f"가격 요소를 찾을 수 없습니다: {str(e)}")
                        price_str = "N/A"
                        exit()

                    # 가격을 정수로 변환 (쉼표 제거, 원 기호 제거)
                    price = 0
                    if price_str != "N/A":
                        try:
                            # '원' 제거 및 쉼표 제거 후 정수로 변환
                            price = int(price_str.replace('원', '').replace(',', ''))
                        except ValueError:
                            self.logger.error(f"가격을 정수로 변환할 수 없습니다: {price_str}")
                            price = 0
                            exit()

                    # 제품 URL 추출
                    try:
                        url_element = element.find_element(By.CSS_SELECTOR, ".shopProductWrapper a")
                        url = url_element.get_attribute("href") if url_element else "N/A"
                    except Exception as e:
                        self.logger.error(f"제품 URL 요소를 찾을 수 없습니다: {str(e)}")
                        url = "N/A"
                        exit()

                    # 제품 이미지 URL 추출
                    try:
                        img_element = element.find_element(By.CSS_SELECTOR, ".thumbDiv .img")
                        img_url = img_element.get_attribute("imgsrc") if img_element else "N/A"
                    except Exception as e:
                        self.logger.error(f"제품 이미지 URL 요소를 찾을 수 없습니다: {str(e)}")
                        img_url = ""
                        exit()

                    # 제품 정보를 딕셔너리로 생성하여 products 배열에 추가
                    product_info = {
                        "title": title,
                        "detail_comment": detail_comment,
                        "price": price,
                        "url": url,
                        "image_url": img_url
                    }

                    products.append(product_info)
                    self.logger.debug(f"제품 정보를 추가했습니다: {title}")
                except Exception as e:
                    self.logger.error(f"제품 정보 추출 중 오류 발생: {str(e)}")
                    exit()

            # 다음 페이지로 이동
            try:
                # 다음 페이지 번호 찾기
                next_page = current_page + 1
                self.logger.info(f"다음 페이지 {next_page}로 이동 시도")

                # 다음 페이지 URL 직접 구성
                try:
                    # 현재 URL에서 페이지 파라미터 변경
                    current_url = self.driver.current_url

                    # 베이핑랩 사이트의 페이징 파라미터 사용
                    # productListFilter=allFilter&productListPage=1&productSortFilter=PRODUCT_ORDER_NO
                    if "productListPage=" in current_url:
                        next_url = current_url.replace(f"productListPage={current_page}", f"productListPage={next_page}")
                    else:
                        # 첫 페이지에 파라미터가 없는 경우 모든 필요한 파라미터 추가
                        if "?" in current_url:
                            next_url = f"{current_url}&productListFilter=allFilter&productListPage={next_page}&productSortFilter=PRODUCT_ORDER_NO"
                        else:
                            next_url = f"{current_url}?productListFilter=allFilter&productListPage={next_page}&productSortFilter=PRODUCT_ORDER_NO"

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
        베이핑랩을 위한 주요 크롤링 메서드.

        Args:
            keywords (list): 이 크롤러에서는 사용되지 않음 (카테고리 기반 크롤링)
            categories (list): 크롤링할 카테고리 목록 (입호흡, 폐호흡)

        Returns:
            dict: 카테고리를 제품 목록에 매핑하는 딕셔너리
        """
        self.logger.info("베이핑랩 크롤링 시작")

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
                crawler = VapingLabCrawler(headless=self.headless, category=category, env_file=self.env_file)
                try:
                    category_products = crawler.get_products()
                    results[category] = category_products
                    self.logger.info(f"카테고리 '{category}'에서 {len(category_products)}개의 제품을 찾았습니다")
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
