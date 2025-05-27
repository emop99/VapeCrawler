import os
import pymysql
from pymysql.cursors import DictCursor
import logging
from dotenv import load_dotenv

class MariaDBConnector:
    """
    MariaDB 데이터베이스에 연결하고 쿼리를 실행하기 위한 클래스
    """

    def __init__(self, host='localhost', port=3306, user='root', password='', database='', charset='utf8mb4', env_file=None):
        """
        MariaDB 연결에 필요한 정보로 초기화합니다.

        Args:
            host (str): 데이터베이스 호스트 주소
            port (int): 데이터베이스 포트 번호
            user (str): 데이터베이스 사용자 이름
            password (str): 데이터베이스 비밀번호
            database (str): 사용할 데이터베이스 이름
            charset (str): 문자셋
            env_file (str, optional): 사용할 .env 파일 경로. 기본값은 None으로, 기본 .env 파일을 사용합니다.
        """
        # 로거 초기화
        self.logger = logging.getLogger(__name__)

        # .env 파일 로드
        if env_file:
            self.logger.info(f"환경 설정 파일 로드: {env_file}")
            load_dotenv(dotenv_path=env_file)
        else:
            self.logger.info("기본 환경 설정 파일 로드")
            load_dotenv()

        self.host = os.getenv('DB_HOST')
        self.port = int(os.getenv('DB_PORT', '3306'))
        self.user = os.getenv('DB_USER')
        self.password = os.getenv('DB_PASSWORD')
        self.database = os.getenv('DB_DATABASE')
        self.charset = charset
        self.connection = None
        self.logger = logging.getLogger(__name__)

    def connect(self):
        """
        MariaDB 데이터베이스에 연결합니다.

        Returns:
            bool: 연결 성공 여부

        Raises:
            pymysql.MySQLError: 데이터베이스 연결 중 오류 발생 시
        """
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset=self.charset,
                cursorclass=DictCursor  # 결과를 딕셔너리 형태로 반환
            )
            self.logger.info("데이터베이스에 성공적으로 연결했습니다.")
            return True
        except pymysql.MySQLError as e:
            self.logger.error(f"데이터베이스 연결 실패: {e}")
            raise

    def disconnect(self):
        """
        데이터베이스 연결을 종료합니다.
        """
        if self.connection and self.connection.open:
            self.connection.close()
            self.logger.info("데이터베이스 연결을 종료했습니다.")
            self.connection = None

    def execute_query(self, query, params=None):
        """
        SQL 쿼리를 실행합니다.

        Args:
            query (str): 실행할 SQL 쿼리
            params (tuple, dict, optional): 쿼리 파라미터

        Returns:
            int: 영향받은 행 수

        Raises:
            pymysql.MySQLError: 쿼리 실행 중 오류 발생 시
        """
        if not self.connection:
            if not self.connect():
                return -1

        try:
            with self.connection.cursor() as cursor:
                affected_rows = cursor.execute(query, params)
                self.connection.commit()
                return affected_rows
        except pymysql.MySQLError as e:
            self.logger.error(f"쿼리 실행 실패: {e}")
            self.connection.rollback()
            raise

    def fetch_all(self, query, params=None):
        """
        SQL 쿼리를 실행하고 모든 결과를 반환합니다.

        Args:
            query (str): 실행할 SQL 쿼리
            params (tuple, dict, optional): 쿼리 파라미터

        Returns:
            list: 쿼리 결과 리스트 또는 None(연결 실패 시)

        Raises:
            pymysql.MySQLError: 쿼리 실행 중 오류 발생 시
        """
        if not self.connection:
            if not self.connect():
                return None

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            self.logger.error(f"쿼리 실행 실패: {e}")
            raise

    def fetch_one(self, query, params=None):
        """
        SQL 쿼리를 실행하고 첫 번째 결과를 반환합니다.

        Args:
            query (str): 실행할 SQL 쿼리
            params (tuple, dict, optional): 쿼리 파라미터

        Returns:
            dict: 쿼리 결과 또는 None(결과가 없거나 연결 실패 시)

        Raises:
            pymysql.MySQLError: 쿼리 실행 중 오류 발생 시
        """
        if not self.connection:
            if not self.connect():
                return None

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchone()
                return result
        except pymysql.MySQLError as e:
            self.logger.error(f"쿼리 실행 실패: {e}")
            raise

    def insert_data(self, table, data):
        """
        테이블에 데이터를 삽입합니다.

        Args:
            table (str): 테이블 이름
            data (dict): 삽입할 데이터(열:값 쌍)

        Returns:
            int: 마지막 삽입 ID 또는 -1(오류 발생 시)
        """
        if not data:
            self.logger.error("삽입할 데이터가 없습니다.")
            return -1

        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        values = tuple(data.values())

        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        if self.execute_query(query, values) > 0:
            insert_id = self.fetch_one('SELECT LAST_INSERT_ID() AS last_id')
            return insert_id['last_id'] if insert_id else -1
        else:
            return -1

    def update_data(self, table, data, condition, condition_params):
        """
        조건에 맞는 데이터를 업데이트합니다.

        Args:
            table (str): 테이블 이름
            data (dict): 업데이트할 데이터(열:값 쌍)
            condition (str): WHERE 조건절
            condition_params (tuple): 조건절 파라미터

        Returns:
            int: 영향받은 행 수 또는 -1(오류 발생 시)
        """
        if not data:
            self.logger.error("업데이트할 데이터가 없습니다.")
            return -1

        set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
        values = tuple(data.values()) + condition_params

        query = f"UPDATE {table} SET {set_clause} WHERE {condition}"

        return self.execute_query(query, values)

    def delete_data(self, table, condition, params):
        """
        조건에 맞는 데이터를 삭제합니다.

        Args:
            table (str): 테이블 이름
            condition (str): WHERE 조건절
            params (tuple): 조건절 파라미터

        Returns:
            int: 영향받은 행 수 또는 -1(오류 발생 시)
        """
        query = f"DELETE FROM {table} WHERE {condition}"
        return self.execute_query(query, params)

    def create_table(self, table, columns_definition):
        """
        새 테이블을 생성합니다.

        Args:
            table (str): 테이블 이름
            columns_definition (str): 열 정의 문자열

        Returns:
            bool: 성공 여부
        """
        query = f"CREATE TABLE IF NOT EXISTS {table} ({columns_definition})"
        return self.execute_query(query) >= 0

    def table_exists(self, table):
        """
        테이블이 존재하는지 확인합니다.

        Args:
            table (str): 테이블 이름

        Returns:
            bool: 테이블 존재 여부
        """
        query = "SHOW TABLES LIKE %s"
        result = self.fetch_one(query, (table,))
        return result is not None

    def get_columns_info(self, table):
        """
        테이블의 열 정보를 가져옵니다.

        Args:
            table (str): 테이블 이름

        Returns:
            list: 열 정보 리스트 또는 None(오류 발생 시)
        """
        query = f"SHOW COLUMNS FROM {table}"
        return self.fetch_all(query)

    def __enter__(self):
        """
        컨텍스트 매니저 진입 메서드
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        컨텍스트 매니저 종료 메서드
        """
        self.disconnect()
