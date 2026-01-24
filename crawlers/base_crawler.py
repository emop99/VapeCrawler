import logging
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
# 로깅 모듈 가져오기
from module.elasticsearch_logger import LoggerFactory


class BaseCrawler:
    """
    Base class for all site-specific crawlers.
    Provides common functionality for web crawling using Selenium Chrome driver.
    """

    def __init__(self, site_name, headless=True, log_level=logging.INFO, env_file='.env'):
        """
        Initialize the base crawler with Selenium Chrome driver.

        Args:
            site_name (str): Name of the site being crawled
            headless (bool): Whether to run Chrome in headless mode
            log_level (int): Logging level
            env_file (str, optional): 환경 변수 파일 경로 (기본값: None)
        """
        self.site_name = site_name
        self.headless = headless  # Store headless setting as instance attribute
        self.env_file = env_file  # 환경 변수 파일 경로 저장
        self.log_level = log_level
        self.setup_logging()
        self.logger.info(f"Initializing crawler for {site_name}")
        self.driver = self.setup_driver(headless)

    def setup_logging(self):
        """Set up logging configuration using class-based logger."""
        # 새로운 클래스 기반 로거 사용
        logger_instance = LoggerFactory.create_elasticsearch_logger(
            f"crawler.{self.site_name}",
            f"VapeCrawler-{self.site_name}",
            log_file='log/vape_crawler.log',
            log_level=self.log_level,
            env_file=self.env_file
        )
        self.logger = logger_instance.get_logger()
        return self.logger

    def setup_driver(self, headless):
        """
        Set up and return a Selenium Chrome driver.

        Args:
            headless (bool): Whether to run Chrome in headless mode

        Returns:
            webdriver.Chrome: Configured Chrome driver
        """
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

        # Initialize Chrome driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        return driver

    def navigate_to(self, url):
        """
        Navigate to the specified URL.

        Args:
            url (str): URL to navigate to

        Returns:
            bool: True if navigation was successful, False otherwise
        """
        try:
            self.logger.info(f"Navigating to {url}")
            self.driver.get(url)
            return True
        except Exception as e:
            self.logger.error(f"Error navigating to {url}: {str(e)}")
            return False

    def wait_for_element(self, by, value, timeout=10):
        """
        Wait for an element to be present on the page.

        Args:
            by (By): Method to locate element
            value (str): Value to search for
            timeout (int): Maximum time to wait in seconds

        Returns:
            WebElement: The found element or None if not found
        """
        try:
            self.logger.debug(f"Waiting for element {by}={value}")
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            self.logger.warning(f"Timeout waiting for element {by}={value}")
            return None
        except Exception as e:
            self.logger.error(f"Error waiting for element {by}={value}: {str(e)}")
            return None

    def find_element(self, by, value):
        """
        Find an element on the page.

        Args:
            by (By): Method to locate element
            value (str): Value to search for

        Returns:
            WebElement: The found element or None if not found
        """
        try:
            return self.driver.find_element(by, value)
        except NoSuchElementException:
            self.logger.warning(f"Element not found: {by}={value}")
            return None
        except Exception as e:
            self.logger.error(f"Error finding element {by}={value}: {str(e)}")
            return None

    def find_elements(self, by, value):
        """
        Find multiple elements on the page.

        Args:
            by (By): Method to locate elements
            value (str): Value to search for

        Returns:
            list: List of found elements or empty list if none found
        """
        try:
            return self.driver.find_elements(by, value)
        except Exception as e:
            self.logger.error(f"Error finding elements {by}={value}: {str(e)}")
            return []

    def parse_price(self, price_str):
        """가격 문자열을 정수로 변환합니다."""
        if not price_str or price_str == "N/A":
            return 0
        try:
            # 괄호와 그 안의 내용을 제거 (보통 할인 정보 등이 들어감)
            # 예: "7,700원 ( 2,200원 할인)" -> "7,700원 "
            price_str = re.sub(r'\(.*?\)', '', price_str)
            # 숫자만 남기고 제거
            price_digits = re.sub(r'[^0-9]', '', price_str)
            return int(price_digits) if price_digits else 0
        except (ValueError, TypeError):
            self.logger.error(f"가격 변환 실패: {price_str}")
            return 0

    def extract_text(self, element, selector, default="N/A"):
        """요소에서 텍스트를 안전하게 추출합니다."""
        try:
            remove_selectors = []
            selector_value = selector
            if isinstance(selector, dict):
                selector_value = selector.get("selector", "")
                remove_selectors = selector.get("remove", []) or []

            if not selector_value:
                found_element = element
            else:
                found_element = element.find_element(By.CSS_SELECTOR, selector_value)

            if not found_element:
                return default

            if remove_selectors:
                script = """
                    const el = arguments[0].cloneNode(true);
                    const removes = arguments[1] || [];
                    removes.forEach(sel => {
                        el.querySelectorAll(sel).forEach(node => node.remove());
                    });
                    return (el.textContent || '').trim();
                """
                text = self.driver.execute_script(script, found_element, remove_selectors)
                return text or default

            return found_element.text.strip() or default
        except Exception:
            return default

    def extract_attribute(self, element, selector, attribute, default=""):
        """요소에서 속성값을 안전하게 추출합니다."""
        try:
            if not selector:
                return element.get_attribute(attribute) or default
            found_element = element.find_element(By.CSS_SELECTOR, selector)
            return found_element.get_attribute(attribute) if found_element else default
        except Exception:
            return default

    def check_sold_out(self, element, selector):
        """품절 여부를 확인합니다."""
        try:
            return bool(element.find_element(By.CSS_SELECTOR, selector))
        except Exception:
            return False

    def get_products_by_selectors(self, selectors):
        """
        셀렉터 설정을 사용하여 제품 정보를 가져옵니다.
        
        selectors = {
            "list": ".prdList > li",
            "title": ".name > a > span",
            "price": ".price",
            "url": ".name > a",
            "image": ".thumb",
            "sold_out": "img[alt='품절']"
            "last_page": ".paging-block .pagination li:last-child a"
        }
        """
        if not self.navigate_to(self.category_url):
            self.logger.error(f"{self.site_name} 카테고리 페이지로 이동 실패")
            return []

        products = []
        seen_urls = set()
        current_page = 1
        
        while True:
            self.logger.info(f"{self.site_name} {self.category} {current_page}페이지 크롤링 중")
            time.sleep(2)
            
            product_elements = self.find_elements(By.CSS_SELECTOR, selectors["list"])
            if not product_elements:
                self.logger.info("페이지에서 제품 요소를 찾을 수 없음 — 크롤링 종료")
                break
                
            self.logger.info(f"{current_page}페이지에서 {len(product_elements)}개 제품 발견")
            
            for element in product_elements:
                try:
                    # 품절 여부 확인
                    if "sold_out" in selectors and self.check_sold_out(element, selectors["sold_out"]):
                        continue

                    # 제목
                    title_selector = selectors["title"]
                    if isinstance(title_selector, dict) and "attribute" in title_selector:
                        title = self.extract_attribute(element, title_selector.get("selector", ""), title_selector["attribute"])
                    else:
                        title = self.extract_text(element, title_selector)

                    if title == "N/A":
                        continue

                    # 가격 (리스트일 경우 순차적으로 시도)
                    price_selectors = selectors["price"] if isinstance(selectors["price"], list) else [selectors["price"]]
                    price_str = "N/A"
                    for ps in price_selectors:
                        if isinstance(ps, dict) and "attribute" in ps:
                            price_str = self.extract_attribute(element, ps.get("selector", ""), ps["attribute"])
                        else:
                            price_str = self.extract_text(element, ps)
                        
                        if price_str != "N/A" and price_str != "":
                            break
                    
                    price = self.parse_price(price_str)

                    # URL
                    url_selector = selectors["url"]
                    if isinstance(url_selector, dict) and "attribute" in url_selector:
                        relative_url = self.extract_attribute(element, url_selector.get("selector", ""), url_selector["attribute"])
                    else:
                        relative_url = self.extract_attribute(element, url_selector, "href")
                    
                    if not relative_url:
                        continue
                        
                    url = relative_url if relative_url.startswith("http") else f"{self.base_url}/{relative_url.lstrip('/')}"

                    # 이미지
                    img_url = ""
                    if "image" in selectors:
                        img_selector = selectors["image"]
                        if isinstance(img_selector, dict) and "attribute" in img_selector:
                            img_url = self.extract_attribute(element, img_selector.get("selector", ""), img_selector["attribute"])
                        else:
                            img_url = self.extract_attribute(element, img_selector, "src")

                    # 중복 상품 체크 (이미 수집된 URL이면 마지막 페이지로 간주하고 종료)
                    if url in seen_urls:
                        self.logger.info(f"중복된 상품 발견 ({title}) - 해당 카테고리 크롤링 종료")
                        return products
                    
                    seen_urls.add(url)

                    products.append({
                        "title": title,
                        "price": price,
                        "url": url,
                        "image_url": img_url,
                        "detail_comment": ""
                    })
                except Exception as e:
                    self.logger.error(f"제품 정보 추출 중 오류: {str(e)}")

            # 끝 페이지 확인 - disabled 클래스를 가진 Next 버튼 확인
            if "last_page" in selectors:
                try:
                    last_page_element = self.find_element(By.CSS_SELECTOR, selectors["last_page"])
                    if last_page_element:
                        self.logger.info(f"마지막 페이지({current_page})에 도달 - 크롤링 종료")
                        break
                except Exception as e:
                    self.logger.debug(f"끝 페이지 확인 중 오류 (무시됨): {str(e)}")

            # 다음 페이지로 이동
            try:
                current_page += 1
                page_param = selectors.get("page_param", "page")
                
                if "next_url_template" in selectors:
                    # 템플릿 사용 (base_url, category_url, page를 변수로 사용 가능)
                    next_url = selectors["next_url_template"].format(
                        base_url=self.base_url,
                        category_url=self.category_url,
                        page=current_page
                    )
                else:
                    if "?" in self.category_url:
                        next_url = f"{self.category_url}&{page_param}={current_page}"
                    else:
                        next_url = f"{self.category_url}?{page_param}={current_page}"
                
                self.logger.info(f"다음 페이지 이동: {next_url}")
                if not self.navigate_to(next_url):
                    break
            except Exception as e:
                self.logger.error(f"다음 페이지 이동 실패: {str(e)}")
                break

        return products

    def crawl(self, keywords=None, categories=None):
        """
        공통 카테고리 순회 크롤링 로직.
        Subclasses should implement get_products().
        """
        self.logger.info(f"{self.site_name} 크롤링 시작")
        results = {}
        
        if categories is None:
            if hasattr(self, 'CATEGORIES'):
                categories = list(self.CATEGORIES.keys())
            else:
                self.logger.error("CATEGORIES가 정의되지 않았습니다.")
                return {}

        for category in categories:
            self.logger.info(f"카테고리 '{category}' 크롤링 중")
            # 현재 카테고리 설정 및 URL 업데이트
            if hasattr(self, 'CATEGORIES') and category in self.CATEGORIES:
                self.category = category
                cat_val = self.CATEGORIES[category]
                
                # base_url과 조합하거나 절대 경로 사용
                if isinstance(cat_val, str) and cat_val.startswith('http'):
                    self.category_url = cat_val
                elif hasattr(self, 'base_url'):
                    if "/product/list.html?cate_no=" not in str(self.category_url): # 이미 경로인 경우
                         self.category_url = f"{self.base_url}{cat_val}"
            
            products = self.get_products()
            results[category] = products
            self.logger.info(f"카테고리 '{category}'에서 {len(products)}개 제품 발견")
            
        return results

    def close(self):
        """
        Close the browser and clean up resources.
        """
        if hasattr(self, 'driver') and self.driver:
            self.logger.info("Closing browser")
            self.driver.quit()
