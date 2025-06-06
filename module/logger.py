#!/usr/bin/env python
"""
logger.py - 로깅 시스템을 위한 베이스 클래스 모듈

이 모듈은 로깅 기능을 제공하는 클래스를 정의합니다.
다양한 로깅 백엔드(파일, Elasticsearch 등)을 지원하도록 설계되었습니다.
"""

import logging
import os
import sys
from abc import ABC, abstractmethod
from dotenv import load_dotenv


class BaseLogger(ABC):
    """
    로깅을 위한 기본 클래스
    이 클래스를 상속받아 다양한 로깅 백엔드(파일, Elasticsearch 등)에 대한 구현 제공
    """

    def __init__(self, logger_name, log_level=logging.INFO, env_file=None):
        """
        기본 로거 초기화

        Args:
            logger_name (str): 로거 이름
            log_level (int): 로깅 레벨 (기본값: logging.INFO)
            env_file (str, optional): 환경 변수 파일 경로 (기본값: None)
        """
        # 환경 변수 로드
        self.env_file = env_file
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        # 로거 설정
        self.logger_name = logger_name
        self.log_level = log_level
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(log_level)
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # 로그 디렉토리 생성
        os.makedirs('log', exist_ok=True)

        # 핸들러 초기화
        self._setup_handlers()

    def _setup_handlers(self):
        """핸들러 설정 (오버라이드 가능)"""
        # 기본적으로 아무 작업도 하지 않음 (하위 클래스에서 구현)
        pass

    @abstractmethod
    def setup_logging(self):
        """로깅 설정 (하위 클래스에서 반드시 구현)"""
        pass

    def get_logger(self):
        """
        설정된 로거 반환

        Returns:
            Logger: 설정된 로거 객체
        """
        return self.logger


class FileLogger(BaseLogger):
    """파일 로깅을 위한 클래스"""

    def __init__(self, logger_name, log_file, log_level=logging.INFO, env_file=None):
        """
        파일 로거 초기화

        Args:
            logger_name (str): 로거 이름
            log_file (str): 로그 파일 경로
            log_level (int): 로깅 레벨 (기본값: logging.INFO)
            env_file (str, optional): 환경 변수 파일 경로 (기본값: None)
        """
        self.log_file = log_file
        super().__init__(logger_name, log_level, env_file)

    def setup_logging(self):
        """파일 로깅 설정"""
        # 이미 핸들러가 있는지 확인
        if not self.logger.handlers:
            # 파일 핸들러 생성 및 추가
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(self.formatter)
            self.logger.addHandler(file_handler)

            # 콘솔 핸들러 생성 및 추가
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(self.formatter)
            self.logger.addHandler(console_handler)

        return self.logger


class LoggerFactory:
    """다양한 로거 인스턴스를 생성하는 팩토리 클래스"""

    @staticmethod
    def create_file_logger(name, log_file, log_level=logging.INFO, env_file=None):
        """
        파일 로거 생성

        Args:
            name (str): 로거 이름
            log_file (str): 로그 파일 경로
            log_level (int): 로깅 레벨 (기본값: logging.INFO)
            env_file (str, optional): 환경 변수 파일 경로 (기본값: None)

        Returns:
            FileLogger: 설정된 파일 로거 인스턴스
        """
        logger = FileLogger(name, log_file, log_level, env_file)
        logger.setup_logging()
        return logger
