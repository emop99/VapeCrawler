#!/usr/bin/env python
"""
VapeRunner - 전자담배 제품 크롤링 및 정렬 자동화 스크립트.

이 스크립트는 VapeCrawler와 VapeSort를 순차적으로 실행하고,
모든 작업이 완료된 후 로그 파일을 정리합니다.
"""
import os
import sys
import logging
import subprocess
import glob
import time
from datetime import datetime
import argparse

# 로깅 모듈 가져오기
from module.elasticsearch_logger import LoggerFactory

# 로깅 디렉토리 생성
os.makedirs('log', exist_ok=True)

# 명령줄 인수 파싱 (로깅 설정을 위해 미리 파싱)
def parse_args():
    parser = argparse.ArgumentParser(description='VapeRunner - 전자담배 제품 크롤링 및 정렬 자동화 스크립트')
    parser.add_argument('--env-file', type=str, help='사용할 .env 파일 경로 (예: .env.development)')
    return parser.parse_known_args()[0]

# 환경 변수 파일 경로 가져오기
pre_args = parse_args()
env_file = getattr(pre_args, 'env_file', '.env')

# 로깅 설정 - 새로운 클래스 기반 로거 사용
logger_instance = LoggerFactory.create_elasticsearch_logger(
    'vape_runner',
    'VapeRunner',
    log_file='log/vape_runner.log',
    env_file=env_file
)
logger = logger_instance.get_logger()

def run_vape_crawler(env_file='.env'):
    """
    VapeCrawler를 실행합니다.

    Args:
        env_file (str, optional): 사용할 .env 파일 경로
    """
    logger.info("VapeCrawler 실행 시작...")
    try:
        # VapeCrawler.py 실행 (환경 변수 파일 경로 전달)
        cmd = [sys.executable, 'VapeCrawler.py']
        if env_file:
            cmd.extend(['--env-file', env_file])

        subprocess.run(cmd, check=True)
        logger.info("VapeCrawler 실행 완료")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"VapeCrawler 실행 중 오류 발생: {e}")
        return False
    except Exception as e:
        logger.error(f"VapeCrawler 실행 중 예상치 못한 오류 발생: {e}")
        return False

def run_vape_sort(env_file='.env'):
    """
    VapeSort를 실행합니다.

    Args:
        env_file (str, optional): 사용할 .env 파일 경로
    """
    logger.info("VapeSort 실행 시작...")
    try:
        # VapeSort.py 실행 (환경 변수 파일 경로 전달)
        cmd = [sys.executable, 'VapeSort.py']
        if env_file:
            cmd.extend(['--env-file', env_file])

        subprocess.run(cmd, check=True)
        logger.info("VapeSort 실행 완료")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"VapeSort 실행 중 오류 발생: {e}")
        return False
    except Exception as e:
        logger.error(f"VapeSort 실행 중 예상치 못한 오류 발생: {e}")
        return False

def clean_json_files():
    """
    results 폴더 내의 모든 .json 파일을 삭제합니다.
    """
    logger.info("JSON 파일 정리 시작...")
    try:
        # results 폴더가 없으면 생성
        os.makedirs('results', exist_ok=True)

        # results 폴더 내의 모든 .json 파일 경로 가져오기
        json_files = glob.glob(os.path.join('results', '*.json'))

        # 삭제된 파일 수 카운트
        deleted_count = 0

        # 각 JSON 파일 삭제
        for json_file in json_files:
            try:
                os.remove(json_file)
                logger.info(f"JSON 파일 삭제: {json_file}")
                deleted_count += 1
            except Exception as e:
                logger.warning(f"JSON 파일 삭제 실패: {json_file} - {e}")

        logger.info(f"총 {deleted_count}개의 JSON 파일 삭제 완료")
        return True
    except Exception as e:
        logger.error(f"JSON 파일 정리 중 오류 발생: {e}")
        return False

def main():
    """
    메인 실행 함수
    """
    # 명령줄 인수 파싱
    import argparse
    parser = argparse.ArgumentParser(description='VapeRunner - 전자담배 제품 크롤링 및 정렬 자동화 스크립트')
    parser.add_argument('--env-file', type=str, help='사용할 .env 파일 경로 (예: .env.development)')
    parser.add_argument('--interval', type=int, help='실행 간격 (분 단위, 예: 60은 1시간마다 실행)')
    args = parser.parse_args()

    # 환경 변수 파일 경로 설정
    env_file = args.env_file
    if env_file:
        logger.info(f"사용자 지정 환경 설정 파일 사용: {env_file}")
        # 환경 변수 파일이 존재하는지 확인
        if not os.path.exists(env_file):
            logger.error(f"지정한 환경 설정 파일이 존재하지 않습니다: {env_file}")
            return
    else:
        logger.info("기본 환경 설정 파일 사용")

    # 실행 간격 설정
    interval = args.interval

    def run_process():
        """실제 작업을 수행하는 내부 함수"""
        start_time = time.time()
        logger.info("VapeRunner 작업 시작")

        # VapeCrawler 실행 (환경 변수 파일 경로 전달)
        crawler_success = run_vape_crawler(env_file)
        if not crawler_success:
            logger.error("VapeCrawler 실행 실패. 프로세스를 중단합니다.")
            return False

        # VapeSort 실행 (환경 변수 파일 경로 전달)
        sort_success = run_vape_sort(env_file)
        if not sort_success:
            logger.error("VapeSort 실행 실패. JSON 파일 정리를 진행합니다.")

        # JSON 파일 정리
        clean_json_files()

        end_time = time.time()
        logger.info(f"VapeRunner 작업 완료. 총 소요 시간: {end_time - start_time:.2f}초")
        return True

    if interval:
        logger.info(f"인터벌 모드 활성화: {interval}분마다 실행")
        try:
            while True:
                run_process()
                logger.info(f"{interval}분 후 다음 실행 예정 (현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
                # 다음 실행까지 대기 (분 단위를 초 단위로 변환)
                time.sleep(interval * 60)
        except KeyboardInterrupt:
            logger.info("사용자에 의해 프로그램이 종료되었습니다.")
    else:
        # 단일 실행 모드
        run_process()

if __name__ == "__main__":
    main()
