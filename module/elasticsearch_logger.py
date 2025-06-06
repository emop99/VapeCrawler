#!/usr/bin/env python
"""
elasticsearch_logger.py - Elasticsearch에 로그를 기록하기 위한 모듈

이 모듈은 표준 Python 로깅과 함께 Elasticsearch에 로그를 저장하는 기능을 제공합니다.
"""

import logging
import os
import json
from datetime import datetime
from elasticsearch import Elasticsearch
import socket
import platform
from dotenv import load_dotenv

from module.logger import BaseLogger

class ElasticsearchHandler(logging.Handler):
    """
    로그 메시지를 Elasticsearch에 저장하는 핸들러
    """

    def __init__(self, host=None, index_name=None,
                 app_name=None, es_auth=None, timeout=60, env_file=None):
        """
        Elasticsearch 핸들러 초기화

        Args:
            host (str): Elasticsearch 호스트 (기본값: .env에서 ES_HOST 또는 'localhost:9200')
            index_name (str): 로그를 저장할 인덱스 이름 (기본값: .env에서 ES_INDEX 또는 'vape_logs')
            app_name (str): 애플리케이션 이름 (기본값: None)
            es_auth (tuple): Elasticsearch 인증 정보 (username, password) (기본값: .env에서 ES_USER와 ES_PASSWORD)
            timeout (int): 연결 타임아웃 (초) (기본값: .env에서 ES_TIMEOUT 또는 60)
            env_file (str): 환경 변수 파일 경로 (기본값: None)
        """
        super().__init__()

        # 환경 변수 로드
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()  # 기본 .env 파일 로드

        # 환경 변수 또는 기본값 설정
        self.host = host or os.getenv("ES_HOST", "localhost:9200")
        self.index_name = index_name or os.getenv("ES_INDEX", "vape_logs")
        self.app_name = app_name
        self.hostname = socket.gethostname()
        self.platform = platform.platform()

        # 인증 정보 처리
        if not es_auth:
            es_user = os.getenv("ES_USER")
            es_password = os.getenv("ES_PASSWORD")
            if es_user and es_password:
                es_auth = (es_user, es_password)

        # 타임아웃 값 처리
        es_timeout = os.getenv("ES_TIMEOUT")
        if es_timeout:
            try:
                timeout = int(es_timeout)
            except ValueError:
                pass

        # Elasticsearch 클라이언트 설정 (Elasticsearch 9.x 버전용)
        es_kwargs = {}

        # 타임아웃 설정 (Elasticsearch 9.x 버전에서는 request_timeout 사용)
        es_kwargs["request_timeout"] = timeout

        # 인증 정보 설정
        if es_auth:
            es_user, es_password = es_auth
            es_kwargs["basic_auth"] = (es_user, es_password)

        # 호스트에서 프로토콜 부분이 있으면 제거 (http://, https:// 등)
        if self.host.startswith(('http://', 'https://')):
            self.host = self.host.split('://', 1)[1]

        # Elasticsearch 클라이언트 초기화 (HTTP 강제 지정)
        self.es = Elasticsearch(f"http://{self.host}", **es_kwargs)

        # 인덱스 존재 여부 확인 및 생성
        try:
            if not self.es.indices.exists(index=self.index_name):
                self.es.indices.create(
                    index=self.index_name,
                    mappings={
                        "properties": {
                            "timestamp": {"type": "date"},
                            "level": {"type": "keyword"},
                            "logger_name": {"type": "keyword"},
                            "message": {"type": "text"},
                            "app_name": {"type": "keyword"},
                            "hostname": {"type": "keyword"},
                            "platform": {"type": "keyword"},
                            "exception": {"type": "text"},
                            "stack_trace": {"type": "text"},
                        }
                    }
                )
        except Exception as e:
            import sys
            sys.stderr.write(f"Elasticsearch 인덱스 생성 중 오류 발생: {e}\n")

    def emit(self, record):
        """
        로그 레코드를 Elasticsearch에 저장합니다.

        Args:
            record: 로그 레코드 객체
        """
        try:
            # 예외 정보 처리
            exc_info = None
            stack_trace = None
            if record.exc_info:
                exc_info = str(record.exc_info[1])
                stack_trace = self.formatter.formatException(record.exc_info)

            # Elasticsearch에 저장할 문서
            log_entry = {
                "timestamp": datetime.utcfromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "logger_name": record.name,
                "message": record.getMessage(),
                "app_name": self.app_name,
                "hostname": self.hostname,
                "platform": self.platform
            }

            if exc_info:
                log_entry["exception"] = exc_info

            if stack_trace:
                log_entry["stack_trace"] = stack_trace

            # Elasticsearch 9.x 버전에서는 document 매개변수 사용
            self.es.index(
                index=self.index_name,
                document=log_entry
            )

        except Exception as e:
            # 핸들러 내부에서 발생한 예외는 stderr로 출력
            # (로깅 루프를 방지하기 위해 logging을 사용하지 않음)
            import sys
            sys.stderr.write(f"Error in ElasticsearchHandler: {e}\n")


class ElasticsearchLogger(BaseLogger):
    """Elasticsearch 로깅을 위한 클래스"""

    def __init__(self, logger_name, app_name, host=None, index_name=None,
                 log_level=logging.INFO, env_file=None, log_file=None):
        """
        Elasticsearch 로거 초기화

        Args:
            logger_name (str): 로거 이름
            app_name (str): 애플리케이션 이름
            host (str): Elasticsearch 호스트 (기본값: .env에서 ES_HOST 또는 'localhost:9200')
            index_name (str): 로그를 저장할 인덱스 이름 (기본값: .env에서 ES_INDEX 또는 'vape_logs')
            log_level (int): 로깅 레벨 (기본값: logging.INFO)
            env_file (str, optional): 환경 변수 파일 경로 (기본값: None)
            log_file (str, optional): 로그 파일 경로 (기본값: None, 지정하면 파일 로깅도 함께 설정)
        """
        self.app_name = app_name
        self.es_host = host
        self.es_index = index_name
        self.log_file = log_file
        super().__init__(logger_name, log_level, env_file)

    def setup_logging(self):
        """Elasticsearch 로깅과 선택적 파일 로깅 설정"""
        # 이미 핸들러가 있는지 확인
        if self.logger.handlers:
            return self.logger

        # 환경 변수 확인하여 개발환경 여부 판단
        run_env = os.getenv("RUN_ENV", "").lower()
        if run_env in ("dev", "development", "local"):
            import sys
            sys.stderr.write(f"[{self.logger_name}] 개발 환경(RUN_ENV={run_env})에서는 Elasticsearch 로깅이 비활성화됩니다.\n")
            # 개발 환경에서는 파일과 콘솔 로깅만 설정
            self._setup_file_console_handlers()
            return self.logger

        # ES_ENABLED 환경 변수 확인
        es_enabled = os.getenv("ES_ENABLED", "true").lower()
        if es_enabled in ("false", "0", "no", "off"):
            import sys
            sys.stderr.write(f"[{self.logger_name}] ES_ENABLED 설정에 따라 Elasticsearch 로깅이 비활성화됩니다.\n")
            # ES_ENABLED가 false면 파일과 콘솔 로깅만 설정
            self._setup_file_console_handlers()
            return self.logger

        # 파일 및 콘솔 로깅 설정
        self._setup_file_console_handlers()

        # Elasticsearch 핸들러 설정
        es_handler = ElasticsearchHandler(
            host=self.es_host,
            index_name=self.es_index,
            app_name=self.app_name,
            env_file=self.env_file
        )

        # 포맷터 설정
        es_handler.setFormatter(self.formatter)

        # 레벨 설정
        es_handler.setLevel(self.log_level)

        # 로거에 핸들러 추가
        self.logger.addHandler(es_handler)

        return self.logger

    def _setup_file_console_handlers(self):
        """파일 및 콘솔 로깅 핸들러 설정"""
        # 파일 핸들러 (log_file이 지정된 경우에만)
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(self.formatter)
            self.logger.addHandler(file_handler)

        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)


class LoggerFactory:
    """로거 인스턴스를 생성하는 팩토리 클래스"""

    @staticmethod
    def create_elasticsearch_logger(name, app_name, log_file=None,
                                    host=None, index_name=None,
                                    log_level=logging.INFO, env_file=None):
        """
        Elasticsearch 로거 생성

        Args:
            name (str): 로거 이름
            app_name (str): 애플리케이션 이름
            log_file (str, optional): 로그 파일 경로 (기본값: None)
            host (str, optional): Elasticsearch 호스트 (기본값: None, .env에서 가져옴)
            index_name (str, optional): 인덱스 이름 (기본값: None, .env에서 가져옴)
            log_level (int): 로깅 레벨 (기본값: logging.INFO)
            env_file (str, optional): 환경 변수 파일 경로 (기본값: None)

        Returns:
            ElasticsearchLogger: 설정된 Elasticsearch 로거 인스턴스
        """
        logger = ElasticsearchLogger(
            name,
            app_name,
            host=host,
            index_name=index_name,
            log_level=log_level,
            env_file=env_file,
            log_file=log_file
        )
        logger.setup_logging()
        return logger


# 기존 인터페이스와의 호환성을 위한 함수 (레거시 지원)
def setup_elasticsearch_logging(logger_name, app_name, host=None,
                               index_name=None, level=logging.INFO, env_file=None):
    """
    Elasticsearch 로깅을 설정합니다. (레거시 함수)

    Args:
        logger_name (str): 로거 이름
        app_name (str): 애플리케이션 이름
        host (str): Elasticsearch 호스트 (기본값: .env에서 ES_HOST 또는 'localhost:9200')
        index_name (str): 로그를 저장할 인덱스 이름 (기본값: .env에서 ES_INDEX 또는 'vape_logs')
        level (int): 로그 레벨 (기본값: logging.INFO)
        env_file (str): 환경 변수 파일 경로 (기본값: None)

    Returns:
        logger: 설정된 로거 객체
    """
    es_logger = LoggerFactory.create_elasticsearch_logger(
        logger_name,
        app_name,
        host=host,
        index_name=index_name,
        log_level=level,
        env_file=env_file
    )
    return es_logger.get_logger()
