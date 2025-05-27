#!/usr/bin/env python
"""
VapeCrawler - 전자담배 제품을 위한 모듈식 웹 크롤러.

이 스크립트는 크롤러를 실행하기 위한 진입점 역할을 합니다.
명령줄 인수에 따라 모든 크롤러 또는 특정 크롤러를 실행할 수 있습니다.
"""
import argparse
import json
import logging
import os
import sys
import time
import threading
from datetime import datetime

# 크롤러 가져오기
from crawlers import VapeMonsterCrawler, VapingLabCrawler, Juice24Crawler, Juice99Crawler, JuiceboxCrawler, JuiceshopCrawler, SkyVapeCrawler

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('log/vape_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('vape_crawler')


def save_results(results, site_name):
    """
    크롤링 결과를 JSON 파일로 저장합니다.

    Args:
        results (dict): 크롤링 결과
        site_name (str): 사이트 이름
    """
    # 결과 디렉토리가 없으면 생성
    os.makedirs('results', exist_ok=True)

    # site_name 한글화 처리
    siteMap = {
        "vapemonster": "베이프몬스터(베몬)",
        "vapinglab": "김성유베이핑연구소(김성유)",
        "juice24": "액상24",
        "juice99": "액상99",
        "juicebox": "쥬스박스",
        "juiceshop": "액상샵",
        "skyvape": "스카이베이프",
    }

    # 타임스탬프가 포함된 파일 이름 생성
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"results/{siteMap[site_name]}_{timestamp}.json"

    # 결과를 파일에 저장
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"Results saved to {filename}")


def run_crawler(crawler_class, keywords, headless, categories=None):
    """
    크롤러를 실행하고 결과를 저장합니다.
    스레드에서 실행할 수 있도록 설계되었습니다.

    Args:
        crawler_class: 인스턴스화할 크롤러 클래스
        keywords (list): 검색할 키워드 목록
        headless (bool): 헤드리스 모드로 실행할지 여부
        categories (list): 크롤링할 카테고리 목록 (VapeMonsterCrawler, VapingLabCrawler, Juice24Crawler, Juice99Crawler, JuiceboxCrawler, JuiceshopCrawler, SkyVapeCrawler에 적용)
    """
    crawler = None
    try:
        # VapeMonsterCrawler, VapingLabCrawler, Juice24Crawler, Juice99Crawler, JuiceboxCrawler, JuiceshopCrawler, SkyVapeCrawler인 경우 카테고리 처리
        if (crawler_class in [VapeMonsterCrawler, VapingLabCrawler, Juice24Crawler, Juice99Crawler, JuiceboxCrawler, JuiceshopCrawler, SkyVapeCrawler]) and categories and len(
                categories) > 0:
            # 첫 번째 카테고리로 인스턴스 생성
            first_category = categories[0]
            logger.info(f"Creating {crawler_class.__name__} with initial category: {first_category}")
            crawler = crawler_class(headless=headless, category=first_category)
            logger.info(f"Running {crawler.site_name} crawler with categories: {categories}")

            # 크롤러 실행 (모든 카테고리 전달)
            start_time = time.time()
            results = crawler.crawl(keywords=keywords, categories=categories)
            end_time = time.time()
        else:
            # 다른 크롤러 또는 카테고리가 지정되지 않은 경우
            crawler = crawler_class(headless=headless)
            logger.info(f"Running {crawler.site_name} crawler")

            # 크롤러 실행
            start_time = time.time()
            results = crawler.crawl(keywords=keywords)
            end_time = time.time()

        # 크롤링 통계 로깅
        total_products = sum(len(products) for products in results.values())
        logger.info(f"Crawling completed in {end_time - start_time:.2f} seconds")
        logger.info(f"Total products found: {total_products}")

        # 결과 저장
        save_results(results, crawler.site_name)

    except Exception as e:
        logger.error(f"Error running crawler: {str(e)}")
    finally:
        # 리소스 정리
        if crawler:
            crawler.close()


def main():
    """스크립트의 주요 진입점."""
    # 명령줄 인수 파싱
    parser = argparse.ArgumentParser(description='VapeCrawler - A modular web crawler for vape products')
    parser.add_argument('--sites', nargs='+', choices=['vapemonster', 'vapinglab', 'juice24', 'juice99', 'juicebox', 'juiceshop', 'skyvape', 'all'], default=['all'],
                        help='Sites to crawl (default: all)')
    parser.add_argument('--keywords', nargs='+', default=['vape'],
                        help='Keywords to search for (default: vape)')
    parser.add_argument('--categories', nargs='+', choices=['입호흡', '폐호흡'],
                        help='Categories to crawl (VapeMonster: 입호흡, 폐호흡 / VapingLab: 입호흡, 폐호흡 / Juice24: 입호흡, 폐호흡 / Juice99: 입호흡, 폐호흡 / Juicebox: 입호흡, 폐호흡 / Juiceshop: 입호흡, 폐호흡 / SkyVape: 입호흡, 폐호흡)')
    parser.add_argument('--no-headless', action='store_true',
                        help='Run browsers in non-headless mode (visible)')
    parser.add_argument('--env-file', type=str,
                        help='Path to the .env file to use (e.g., .env.development)')
    args = parser.parse_args()

    # 크롤링할 사이트 결정
    sites_to_crawl = []
    if 'all' in args.sites:
        sites_to_crawl = ['vapemonster', 'vapinglab', 'juice24', 'juice99', 'juicebox', 'juiceshop', 'skyvape']
    else:
        sites_to_crawl = args.sites

    # 사이트 이름을 크롤러 클래스에 매핑
    crawler_map = {
        'vapemonster': VapeMonsterCrawler,
        'vapinglab': VapingLabCrawler,
        'juice24': Juice24Crawler,
        'juice99': Juice99Crawler,
        'juicebox': JuiceboxCrawler,
        'juiceshop': JuiceshopCrawler,
        # 'skyvape': SkyVapeCrawler //TODO 로그인 프로세스 필요
    }

    # 크롤링 매개변수 로깅
    logger.info(f"Starting crawling with parameters:")
    logger.info(f"Sites: {sites_to_crawl}")
    logger.info(f"Keywords: {args.keywords}")
    if args.categories:
        logger.info(f"Categories: {args.categories}")
    logger.info(f"Headless mode: {not args.no_headless}")

    # 스레드 리스트 초기화
    threads = []

    # 각 사이트별로 스레드 생성
    for site in sites_to_crawl:
        if site in crawler_map:
            # 스레드 생성
            if (site == 'vapemonster' or site == 'vapinglab' or site == 'juice24' or site == 'juice99' or site == 'juicebox' or site == 'juiceshop') and args.categories:
                thread = threading.Thread(
                    target=run_crawler,
                    args=(crawler_map[site], args.keywords, not args.no_headless, args.categories),
                    name=f"{site}_thread"
                )
            else:
                thread = threading.Thread(
                    target=run_crawler,
                    args=(crawler_map[site], args.keywords, not args.no_headless),
                    name=f"{site}_thread"
                )

            # 스레드 시작
            logger.info(f"Starting thread for {site} crawler")
            thread.start()
            threads.append(thread)
        else:
            logger.warning(f"No crawler implemented for site: {site}")

    # 모든 스레드가 완료될 때까지 대기
    for thread in threads:
        logger.info(f"Waiting for {thread.name} to complete...")
        thread.join()
        logger.info(f"{thread.name} completed")

    logger.info("All crawling tasks completed")


if __name__ == "__main__":
    main()
