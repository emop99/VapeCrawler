"""
푸시 알림 모듈
"""
from __future__ import annotations
import os
import json
import logging
from typing import Optional

try:
    # 선택적 의존성: 프로젝트에 존재할 때만 사용합니다
    from module.elasticsearch_logger import LoggerFactory  # type: ignore
    _logger_instance = LoggerFactory.create_elasticsearch_logger(
        'push_alarm', 'PushAlarm', log_file='log/push_alarm.log', env_file=os.getenv('ENV_FILE', '.env')
    )
    logger = _logger_instance.get_logger()
except Exception:
    # Elasticsearch 로거를 사용할 수 없는 경우 표준 로거로 대체합니다
    logger = logging.getLogger('PushAlarm')
    if not logger.handlers:
        os.makedirs('log', exist_ok=True)
        handler = logging.FileHandler('log/push_alarm.log', encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

try:
    import requests
except Exception as e:
    requests = None  # type: ignore
    logger.warning(f"requests 라이브러리를 불러오지 못했습니다: {e}. 푸시 알림이 비활성화됩니다.")

DEFAULT_ENDPOINT = '/api/notifications/admin'


def _build_url(base_url: Optional[str], endpoint: str) -> str:
    if base_url:
        return base_url.rstrip('/') + endpoint
    return endpoint  # 상대 경로(리버스 프록시 등 환경에 의존할 수 있음)


def send_push(message: str, base_url: Optional[str] = None, api_key: Optional[str] = None, timeout: int = 10) -> bool:
    """
    관리자 알림 엔드포인트로 푸시 알림을 전송합니다.

    인자:
        message: 전송할 알림 메시지 텍스트
        base_url: API 기본 URL. None이면 환경변수 PUSH_BASE_URL을 사용하고, 여전히 None이면 상대 경로를 사용합니다.
        api_key: x-api-key 헤더에 사용할 API 키. None이면 환경변수 PUSH_API_KEY 또는 기본값을 사용합니다.
        timeout: HTTP 타임아웃(초)

    반환값:
        요청이 성공적으로 처리된 것으로 보이면(True: HTTP 2xx), 아니면 False를 반환합니다.
    """
    if not message:
        logger.warning('빈 메시지는 전송하지 않습니다.')
        return False

    if requests is None:
        logger.error('requests 라이브러리가 없어 푸시 알림 전송을 건너뜁니다.')
        return False

    base_url = base_url or os.getenv('PUSH_BASE_URL')
    api_key = api_key or os.getenv('PUSH_API_KEY')
    url = _build_url(base_url, DEFAULT_ENDPOINT)

    headers = {
        'Content-Type': 'application/json',
        'x-api-key': api_key,
    }
    data = {'message': message}

    try:
        resp = requests.post(url, headers=headers, data=json.dumps(data), timeout=timeout)
        if 200 <= resp.status_code < 300:
            logger.info(f"푸시 알림 전송 성공: {message}")
            return True
        else:
            logger.error(f"푸시 알림 전송 실패: status={resp.status_code}, body={resp.text}")
            return False
    except Exception as e:
        logger.error(f"푸시 알림 전송 중 오류: {e}")
        return False


# 자주 사용하는 표준 이벤트용 헬퍼 함수

def notify_runner_complete(duration_seconds: Optional[float] = None) -> bool:
    msg = 'VapeRunner 작업이 완료되었습니다.'
    if duration_seconds is not None:
        msg += f" 총 소요 시간: {duration_seconds:.2f}초"
    return send_push(msg)


def notify_runner_error(context: Optional[str] = None) -> bool:
    msg = 'VapeRunner 작업 중 오류가 발생했습니다.'
    if context:
        msg += f" 상세: {context}"
    return send_push(msg)


def notify_crawler_empty(site_name: str) -> bool:
    # site_name은 VapeCrawler에서 사용 중인 한글화 이름 또는 코드명을 받을 수 있음
    msg = f"{site_name} 크롤링 결과에 상품이 없습니다."
    return send_push(msg)


__all__ = [
    'send_push',
    'notify_runner_complete',
    'notify_runner_error',
    'notify_crawler_empty',
]
