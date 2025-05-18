import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class BaseCrawler:
    """
    Base class for all site-specific crawlers.
    Provides common functionality for web crawling using Selenium Chrome driver.
    """

    def __init__(self, site_name, headless=True, log_level=logging.INFO):
        """
        Initialize the base crawler with Selenium Chrome driver.

        Args:
            site_name (str): Name of the site being crawled
            headless (bool): Whether to run Chrome in headless mode
            log_level (int): Logging level
        """
        self.site_name = site_name
        self.headless = headless  # Store headless setting as instance attribute
        self.setup_logging(log_level)
        self.logger.info(f"Initializing crawler for {site_name}")
        self.driver = self.setup_driver(headless)

    def setup_logging(self, log_level):
        """Set up logging configuration."""
        self.logger = logging.getLogger(f"crawler.{self.site_name}")
        self.logger.setLevel(log_level)

        # Create handlers if they don't exist
        if not self.logger.handlers:
            # Create file handler
            file_handler = logging.FileHandler('log/vape_crawler.log', encoding='utf-8')
            file_handler.setLevel(log_level)

            # Create console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)

            # Create formatter
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            # Add handlers to logger
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

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

    def crawl(self):
        """
        Main crawling method to be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement the crawl method")

    def close(self):
        """
        Close the browser and clean up resources.
        """
        if hasattr(self, 'driver') and self.driver:
            self.logger.info("Closing browser")
            self.driver.quit()
