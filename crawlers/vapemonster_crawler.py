"""
베이프몬스터 크롤러 구현.
"""
import time
from selenium.webdriver.common.by import By
from .base_crawler import BaseCrawler


class VapeMonsterCrawler(BaseCrawler):
    """
    베이프몬스터 웹사이트용 크롤러.
    """

    # 카테고리 코드 매핑
    CATEGORIES = {
        "입호흡": "006",
        "폐호흡": "007",
        "무니코틴": "014",
    }

    def __init__(self, headless=True, category="입호흡"):
        """
        베이프몬스터 크롤러를 초기화합니다.

        Args:
            headless (bool): 크롬을 헤드리스 모드로 실행할지 여부
            category (str): 크롤링할 카테고리 (입호흡, 폐호흡, 무니코틴)
        """
        super().__init__("vapemonster", headless)
        self.base_url = "https://www.vapemonster.co.kr"

        # 카테고리 코드 가져오기 (없으면 기본값 사용)
        category_code = self.CATEGORIES.get(category, self.CATEGORIES["입호흡"])
        self.category = category
        self.category_code = category_code
        self.category_url = f"{self.base_url}/goods/goods_list.php?cateCd={category_code}"

    def get_products(self):
        """
        베이프몬스터에서 제품을 가져옵니다.
        페이지 파라미터 값을 +1씩 증가시키면서 상품 정보가 있는 한 계속 크롤링합니다.

        Returns:
            list: 제품 정보 딕셔너리 목록
        """
        if not self.navigate_to(self.category_url):
            self.logger.error("베이프몬스터 카테고리 페이지로 이동하지 못했습니다")
            return []

        # 페이지가 로드될 때까지 대기
        time.sleep(2)

        products = []
        current_page = 1
        has_products = True

        while has_products:
            self.logger.info(f"베이프몬스터 {self.category} 카테고리의 {current_page} 페이지 크롤링 중")

            # 제품 요소가 로드될 때까지 대기
            time.sleep(2)

            # 모든 제품 요소 찾기
            product_elements = self.find_elements(By.CSS_SELECTOR, "div.item_cont")

            if not product_elements:
                self.logger.warning("페이지에서 제품 요소를 찾을 수 없습니다")
                has_products = False
                break

            self.logger.info(f"{current_page} 페이지에서 {len(product_elements)}개의 제품을 찾았습니다")

            # 제품 정보 추출
            for element in product_elements:
                try:
                    # 제품 제목 추출
                    title_element = element.find_element(By.CSS_SELECTOR, "div.item_tit_box a")
                    full_title = title_element.text.strip() if title_element else "N/A"

                    # 제목과 상세 설명 분리
                    if "\n" in full_title:
                        title_parts = full_title.split("\n", 1)
                        title = title_parts[0]
                        detail_comment = title_parts[1]
                    else:
                        title = full_title
                        detail_comment = ""

                    # 제품 가격 추출
                    price_element = element.find_element(By.CSS_SELECTOR, "div.item_money_box strong")
                    price_str = price_element.text.strip() if price_element else "N/A"

                    # 가격을 정수로 변환 (쉼표 제거, 원 기호 제거)
                    price = 0
                    if price_str != "N/A":
                        try:
                            # '원' 제거 및 쉼표 제거 후 정수로 변환
                            price = int(price_str.replace('원', '').replace(',', ''))
                        except ValueError:
                            self.logger.warning(f"가격을 정수로 변환할 수 없습니다: {price_str}")
                            price = 0

                    # 제품 URL 추출
                    url = title_element.get_attribute("href") if title_element else "N/A"

                    # 제품 이미지 URL 추출
                    img_element = element.find_element(By.CSS_SELECTOR, "div.item_photo_box img")
                    img_url = img_element.get_attribute("src") if img_element else "N/A"

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

                # 방법 3: 다음 페이지 URL 직접 구성 (가장 안정적인 방법)
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
        베이프몬스터를 위한 주요 크롤링 메서드.

        Args:
            keywords (list): 이 크롤러에서는 사용되지 않음 (카테고리 기반 크롤링)
            categories (list): 크롤링할 카테고리 목록 (입호흡, 폐호흡, 무니코틴)

        Returns:
            dict: 카테고리를 제품 목록에 매핑하는 딕셔너리
        """
        self.logger.info("베이프몬스터 크롤링 시작")

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
                crawler = VapeMonsterCrawler(headless=self.headless, category=category)
                try:
                    category_products = crawler.get_products()
                    results[category] = category_products
                    self.logger.info(f"카테고리 '{category}'에서 {len(category_products)}개의 제품을 찾았습니다")
                finally:
                    # 리소스 정리
                    crawler.close()
            else:
                # 현재 인스턴스로 크롤링
                self.logger.info(f"카테고리 '{self.category}' (코드: {self.category_code}) 크롤링 중")
                products = self.get_products()
                results[category] = products
                self.logger.info(f"카테고리 '{self.category}'에서 {len(products)}개의 제품을 찾았습니다")

        return results
