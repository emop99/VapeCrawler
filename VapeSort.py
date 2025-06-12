import json
import logging
import re
import os
import argparse
from module.MariaDBConnector import MariaDBConnector
import Levenshtein
import concurrent.futures
from pykospacing import Spacing  # PyKoSpacing 라이브러리 추가
# 로깅 모듈 가져오기
from module.elasticsearch_logger import LoggerFactory

"""
VapeSort.py - 베이프 상품 정보 정렬 및 그룹화 스크립트
"""

# DB 연결
_db = None
# 브랜드 목록 캐시 (메모리 캐싱)
_brand_cache = None

# 로깅 디렉토리 생성
os.makedirs('log', exist_ok=True)


# 명령줄 인수 파싱 (로깅 설정을 위해 미리 파싱)
def parse_args():
    parser = argparse.ArgumentParser(description='VapeSort - 베이프 상품 정보 정렬 및 그룹화 스크립트')
    parser.add_argument('--env-file', type=str, help='사용할 .env 파일 경로 (예: .env.development)')
    return parser.parse_known_args()[0]


# 환경 변수 파일 경로 가져오기
pre_args = parse_args()
env_file = getattr(pre_args, 'env_file', '.env')

# 로깅 설정 - 새로운 클래스 기반 로거 사용
logger_instance = LoggerFactory.create_elasticsearch_logger(
    'vape_sort',
    'VapeSort',
    log_file='log/vape_sort.log',
    env_file=env_file
)
logger = logger_instance.get_logger()


def get_vape_brands_from_db():
    global _brand_cache, _db

    try:
        if _brand_cache is not None:
            return _brand_cache

        # vape_company 테이블에서 브랜드 이름 가져오기
        query = "SELECT id, name FROM vapesite.vape_company"
        result = _db.fetch_all(query)

        if not result:
            logger.error(f"브랜드 데이터가 없습니다: 프로그램을 종료합니다.")
            exit(1)

        # 결과에서 브랜드 이름만 추출하여 리스트로 반환
        brands = {item['name']: {'id': item['id'], 'name': item['name']} for item in result}
        _brand_cache = brands
        logger.info(f"데이터베이스에서 {len(brands)}개의 브랜드를 가져왔습니다.")
        return brands

    except Exception as e:
        logger.error(f"브랜드 데이터 가져오기 오류: {e}")
        logger.error(f"프로그램을 종료합니다.")
        exit(1)


def get_vape_seller_from_db():
    global _db

    try:
        query = "SELECT id, name FROM vapesite.vape_seller_site"
        result = _db.fetch_all(query)

        if not result:
            logger.error(f"판매 사이트 데이터가 없습니다: 프로그램을 종료합니다.")
            exit(1)

        seller_site_list = {item['name']: {'id': item['id'], 'name': item['name']} for item in result}
        logger.info(f"데이터베이스에서 {len(seller_site_list)}개의 판매 사이트를 가져왔습니다.")
        return seller_site_list

    except Exception as e:
        logger.error(f"판매 사이트 리스트 가져오기 오류: {e}")
        logger.error(f"프로그램을 종료합니다.")
        exit(1)


def get_vape_product_category_from_db():
    global _db

    try:
        query = "SELECT id, name FROM vapesite.vape_product_category"
        result = _db.fetch_all(query)

        if not result:
            logger.error(f"상품 카테고리 데이터가 없습니다")
            exit(1)

        product_category_list = {item['name']: {'id': item['id'], 'name': item['name']} for item in result}
        logger.info(f"데이터베이스에서 {len(product_category_list)}개의 카테고리를 가져왔습니다.")
        return product_category_list

    except Exception as e:
        logger.error(f"상품 카테고리 가져오기 오류: {e}")
        logger.error(f"프로그램을 종료합니다.")
        exit(1)


# --- 1단계: 상품명 정규화 및 특징 추출 함수 ---

def normalize_title_text(text):
    """상품명을 정규화합니다."""
    if not text:
        return ""
    text = text.lower()  # 소문자 변환

    # "| 액상샵" 등과 같은 판매처별 태그 제거
    text = re.sub(r'\s*\|\s*.*$', '', text)
    # 대괄호, 소괄호 제거 (내용물은 유지하지 않음 - 필요시 수정)
    text = re.sub(r'[\[\]()]', '', text)
    # "정품", "새상품", "입호흡", "폐호흡" 등의 일반적인 단어 제거 (도메인에 따라 추가/수정)
    # "입호흡", "폐호흡"은 상품 유형을 나타내므로, 별도 필드로 관리하거나, 상품명 정규화 시 제거할 수 있습니다.
    # 여기서는 상품명에서 제거하고, 파일의 카테고리 키("입호흡", "폐호흡")를 활용합니다.
    common_words_to_remove = ["정품", "새상품", "입호흡", "폐호흡", "액상샵", "특가", "할인" "★", "저농도"]
    for word in common_words_to_remove:
        text = text.replace(word, "")

    # 특정 브랜드 처리
    text = re.sub(r'juice box', 'juicebox', text)
    text = re.sub(r'플렉스 x', '플렉스x', text)
    text = re.sub(r'nasty', '네스티', text)
    text = re.sub(r'must', '머스트', text)
    text = re.sub(r'vip(?!쥬스)', 'vip쥬스', text)
    text = re.sub(r'알케마스터(?!\s)', '알케마스터 ', text)
    text = re.sub(r'레인보우 리퀴드', '레인보우리퀴드', text)
    text = re.sub(r'더 블랙', '더블랙', text)
    text = re.sub(r'blvk', '블랙유니콘', text)
    text = re.sub(r'블랙유니콘액상 blvk', '블랙유니콘', text)

    # 제품명 처리
    text = re.sub(r'mint', '민트', text)
    text = re.sub(r'fuji', '후지', text)
    text = re.sub(r'^new\s+', '', text)  # Remove 'new' prefix

    # 제품명에서 용량 문구 제외 처리
    text = re.sub(r'(\d+\.?\d*)\s*(mg/ml|mg|ml|%|)', '', text)
    text = re.sub(r' \.', '', text)
    text = re.sub(r' ,', '', text)

    # 제품명에서 니코틴 농도 문구 제외 처리
    text = re.sub(r'(\d+(\.\d+)?)\s*(mg/ml|mg|%|니코틴|s-nic|rs-nic)', '', text)

    # 공백 표준화 (연속 공백 -> 단일 공백, 양 끝 공백 제거)
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def normalize_product_grouping_key(normalized_title):
    """
    상품명에서 그룹핑 키를 정규화합니다.
    - 상품명에 모든 특수 문자 제거
    - 소문자로 변환
    - PyKoSpacing을 이용하여 자동 띄어쓰기 적용
    - 정규화된 상품명에 띄어쓰기 기준으로 분리하여 내림차순 정렬합니다.
    """
    # 특수 문자 제거 (알파벳, 숫자, 한글, 공백만 허용)
    normalized_title = re.sub(r'[^a-zA-Z0-9가-힣\s]', '', normalized_title)

    # 소문자로 변환
    normalized_title = normalized_title.lower()

    # 모든 공백 제거
    normalized_title = re.sub(r'\s+', ' ', normalized_title).strip()

    # PyKoSpacing을 이용한 자동 띄어쓰기 적용
    spacing = Spacing()
    normalized_title = spacing(normalized_title)

    # 띄어쓰기 기준으로 분리 후 내림차순 정렬
    words = normalized_title.split()
    sorted_words = sorted(words, reverse=True)
    normalized_title = ' '.join(sorted_words)

    # 모든 공백 제거
    normalized_title = re.sub(r'\s+', ' ', normalized_title).strip()

    # 띄어쓰기 기준으로 분리 후 내림차순 정렬
    words = normalized_title.split()
    sorted_words = sorted(words, reverse=True)
    return ' '.join(sorted_words)


def get_company_id_from_title(title):
    """
    상품명에서 회사 ID를 추출합니다.
    """
    normalized_title = normalize_title_text(title)
    known_brands = get_vape_brands_from_db()

    for brand_name, brand_info in known_brands.items():
        if brand_name.lower() in normalized_title:
            return brand_info['id']  # 브랜드 ID 반환

    return 1  # 기본값 (알 수 없는 경우)


def compute_levenshtein_similarity(str1, str2):
    """Levenshtein 유사도(0~1) 반환"""
    if not str1 or not str2:
        return 0.0
    dist = Levenshtein.distance(str1, str2)
    max_len = max(len(str1), len(str2))
    if max_len == 0:
        return 1.0
    return 1 - dist / max_len


def group_products_by_similarity(all_category_products, threshold=0.85):
    """Levenshtein 유사도 기반 그룹핑 (최적화 버전)"""
    # 유사도 계산 결과 캐싱
    similarity_cache = {}

    def cached_similarity(str1, str2):
        """캐시된 Levenshtein 유사도 계산"""
        key = (str1, str2) if str1 < str2 else (str2, str1)
        if key not in similarity_cache:
            similarity_cache[key] = compute_levenshtein_similarity(str1, str2)
        return similarity_cache[key]

    def prefilter_candidates(title_i, all_titles, length_ratio=0.3):
        """빠른 사전 필터링으로 비교 대상 줄이기"""
        len_i = len(title_i)
        candidates = []
        for j, title_j in enumerate(all_titles):
            # 길이 차이가 크면 건너뛰기
            len_j = len(title_j)
            if abs(len_i - len_j) / max(len_i, len_j) > length_ratio:
                continue
            # 문자 집합 유사도로 빠르게 필터링
            set_i, set_j = set(title_i), set(title_j)
            if len(set_i.intersection(set_j)) / len(set_i.union(set_j)) >= 0.5:
                candidates.append(j)
        return candidates

    def process_product(args):
        i, prod_i, products, used, normalized_titles = args
        if i in used:
            return None

        group = [prod_i]
        title_i = normalized_titles[i]
        local_used = set()

        # 사전 필터링으로 후보 줄이기
        candidates = prefilter_candidates(title_i, normalized_titles)

        # 필터링된 후보들만 유사도 계산
        for j in candidates:
            if i == j or j in used or j in local_used:
                continue
            sim = cached_similarity(title_i, normalized_titles[j])
            if sim >= threshold:
                group.append(products[j])
                local_used.add(j)

        return (i, group, local_used)

    def process_category(args):
        category, products = args
        groups = []
        used = set()

        # 모든 제목 정규화 작업 미리 수행
        normalized_titles = [normalize_title_text(p.get('title', '')) for p in products]

        # 배치 처리를 위한 크기 계산
        batch_size = min(1000, len(products))
        batches = [products[i:i + batch_size] for i in range(0, len(products), batch_size)]

        for batch in batches:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(
                        process_product,
                        (products.index(prod_i), prod_i, products, used, normalized_titles)
                    )
                    for prod_i in batch if products.index(prod_i) not in used
                ]

                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result is None:
                        continue
                    i, group, local_used = result
                    used.add(i)
                    used.update(local_used)
                    groups.append(group)

        return groups

    all_groups = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(process_category, all_category_products.items()))
        for group_list in results:
            all_groups.extend(group_list)

    return all_groups


def load_and_integrate_products(file_paths):
    """여러 JSON 파일에서 상품 정보를 로드하고 카테고리별로 그룹화하여 반환합니다."""
    category_grouped_products = {}
    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                file_name_simple = os.path.basename(file_path).split('_')[0]  # 예: "juice24"

                for product_type, products in data.items():  # "입호흡", "폐호흡" 등 카테고리
                    if isinstance(products, list):
                        for product in products:
                            product['source_file'] = file_name_simple
                            product['product_type'] = product_type  # 상품 유형 추가
                            if product_type not in category_grouped_products:
                                category_grouped_products[product_type] = []
                            category_grouped_products[product_type].append(product)
        except FileNotFoundError:
            logger.error(f"오류: 파일을 찾을 수 없습니다 - {file_path}")
        except json.JSONDecodeError:
            logger.error(f"오류: JSON 디코딩 실패 - {file_path}")
        except Exception as e:
            logger.error(f"파일 처리 중 오류 발생 ({file_path}): {e}")
    return category_grouped_products


# --- 실행 ---
if __name__ == "__main__":
    # 명령줄 인수 파싱
    import argparse

    parser = argparse.ArgumentParser(description='VapeSort - 베이프 상품 정보 정렬 및 그룹화 스크립트')
    parser.add_argument('--env-file', type=str, help='사용할 .env 파일 경로 (예: .env.development)')
    args = parser.parse_args()

    # 환경 변수 파일 경로 설정
    env_file = args.env_file
    if env_file:
        logger.info(f"사용자 지정 환경 설정 파일 사용: {env_file}")
        # 환경 변수 파일이 존재하는지 확인
        if not os.path.exists(env_file):
            logger.error(f"지정한 환경 설정 파일이 존재하지 않습니다: {env_file}")
            exit(1)
    else:
        logger.info("기본 환경 설정 파일 사용")

    # ../results 폴더 내 json 파일 불러오기
    uploaded_file_references = []
    results_dir = os.path.join("results")
    for filename in os.listdir(results_dir):
        if filename.endswith(".json"):
            uploaded_file_references.append(f"results/{filename}")

    # 현재 스크립트가 실행되는 디렉토리를 기준으로 파일 경로를 구성합니다.
    # 실제 파일이 있는 경로로 수정해야 합니다.
    current_directory = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
    file_paths = [os.path.join(current_directory, fname) for fname in uploaded_file_references]

    # 파일이 존재하는지 확인 (실제 환경에서는 파일 존재 유무를 반드시 확인해야 함)
    existing_file_paths = [fp for fp in file_paths if os.path.exists(fp)]
    if not existing_file_paths:
        logger.error(f"오류: 지정된 경로에 JSON 파일이 없습니다. 파일 경로를 확인해주세요.")
        logger.error(f"검색 경로: {current_directory}")
        logger.error(f"예상 파일명: {uploaded_file_references}")
        exit()

    # 데이터베이스 연결 (환경 변수 파일 경로 전달)
    _db = MariaDBConnector(env_file=env_file)
    if not _db.connect():
        logger.error("데이터베이스 연결 실패")
        exit()

    all_category_products = load_and_integrate_products(existing_file_paths)

    if not all_category_products:
        logger.error(f"로드된 상품이 없습니다. JSON 파일 내용이나 구조를 확인해주세요.")
        exit()

    logger.info(f"총 {sum(len(products) for products in all_category_products.values())}개의 상품 정보를 통합했습니다.")

    # 1차: 유사도 기반 그룹핑
    final_grouped_products = group_products_by_similarity(all_category_products, threshold=0.95)

    seller_site_list = get_vape_seller_from_db()
    product_category_list = get_vape_product_category_from_db()
    for products_in_group in final_grouped_products:
        # 1차: 상품 정보 저장
        try:
            visible_product_name = normalize_title_text(products_in_group[0].get('title', ''))
            company_id = get_company_id_from_title(visible_product_name)
            product_category_id = product_category_list[products_in_group[0]['product_type']]['id']
            normalize_product_grouping_name = normalize_product_grouping_key(visible_product_name)

            if company_id == 1:
                logger.warning(f"알 수 없는 회사 입니다. 전체상품명: {products_in_group[0].get('title', '')} 정규화상품명: {visible_product_name}")

            try:
                # 기존 등록된 가격 비교 상품 주소인지 확인
                grouping_product_id = None
                for product in products_in_group:
                    seller_url = product.get('url', '')
                    query = "SELECT productId, sellerId FROM vapesite.vape_price_comparisons WHERE sellerUrl = %s LIMIT 1"
                    existing_product = _db.fetch_one(query, [seller_url])
                    if existing_product:
                        grouping_product_id = existing_product['productId']
                        logger.info(f"기존 가격 비교 상품 주소로 처리: {seller_url} -> 상품 ID={grouping_product_id}")
                        break

                if grouping_product_id:
                    query = "SELECT id, visibleName, productGroupingName FROM vapesite.vape_products WHERE id = %s"
                    product = _db.fetch_one(query, [grouping_product_id])
                else:
                    query = "SELECT id, visibleName, productGroupingName FROM vapesite.vape_products WHERE companyId = %s AND productGroupingName = %s AND productCategoryId = %s"
                    product = _db.fetch_one(query, (company_id, normalize_product_grouping_name, product_category_id))

                if product:
                    # 기존 등록된 상품 정보로 처리
                    logger.info(f"기존 상품 정보 조회 성공: ID={product['id']}, 노출상품명={product['visibleName']}, 그룹상품명={product['productGroupingName']}")
                    grouping_product_id = product['id']
                else:
                    # 신규 상품 정보 등록
                    try:
                        image_url = products_in_group[0].get('image_url', '')

                        # 이미지 URL이 없는 경우 있는 URL 검사
                        if not image_url:
                            for product in products_in_group:
                                if product.get('image_url'):
                                    image_url = product['image_url']
                                    break

                        product_data = {
                            'companyId': company_id,
                            'productCategoryId': product_category_id,
                            'visibleName': visible_product_name,
                            'productGroupingName': normalize_product_grouping_name,
                            'imageUrl': image_url
                        }

                        grouping_product_id = _db.insert_data('vapesite.vape_products', product_data)
                        logger.info(f"기존 상품 정보 조회 없음 상품 저장 처리: 노출상품명={visible_product_name} 그룹상품명={normalize_product_grouping_name}")
                    except Exception as e:
                        logger.error(f"신규 상품 정보 저장 중 오류 발생: {e}")
                        exit()
            except Exception as select_error:
                logger.error(f"기존 상품 정보 조회 중 오류 발생: {select_error}")
                exit()
        except Exception as e:
            error_str = str(e)

            # 다른 종류의 오류인 경우 프로그램 종료
            logger.error(f"상품 저장 중 오류 발생: {e}")
            exit()

        # 2차: 가격 비교 데이터 저장
        for product in products_in_group:
            try:
                seller_site_id = seller_site_list.get(product.get('source_file', ''), {}).get('id', 1)
                seller_url = product.get('url', '')
                new_price = product.get('price', 0)
                title = product.get('title', '')

                if not seller_site_id:
                    logger.error(f"검색된 판매 사이트 정보가 없습니다. 상품 상세 정보: {json.dumps(product, ensure_ascii=False, indent=2)}")
                    continue

                # 판매 사이트별 현재 가격 정보 테이블에 저장할 데이터 준비
                price_comparison_data = {
                    'productId': grouping_product_id,
                    'sellerId': seller_site_id,
                    'sellerUrl': seller_url,
                    'price': new_price,
                    'originTitle': title,
                }

                # 이미 존재하는지 확인
                query = "SELECT id, price FROM vapesite.vape_price_comparisons WHERE productId = %s AND sellerUrl = %s AND sellerId = %s LIMIT 1"
                existing_price = _db.fetch_one(query, [grouping_product_id, seller_url, seller_site_id])

                if existing_price:
                    price_comparison_id = existing_price['id']
                    # 현재 가격 정보가 있는 경우 가격 비교 데이터 처리
                    old_price = existing_price['price']

                    # 가격이 변경된 경우 업데이트
                    if old_price != new_price:
                        lowest_price_search_query = "SELECT price FROM vapesite.vape_price_comparisons WHERE productId = %s ORDER BY price ASC LIMIT 1"

                        # 상품의 업데이트 이전 최저가 가격 가져오기
                        old_lowest_price = _db.fetch_one(lowest_price_search_query, [grouping_product_id])

                        # 판매 사이트 현재 가격 정보 업데이트
                        _db.update_data(
                            'vapesite.vape_price_comparisons',
                            {'price': new_price, 'sellerUrl': seller_url, 'originTitle': title},
                            'id = %s',
                            (price_comparison_id,)
                        )

                        # 상품의 가격 업데이트 이후 최저가 가격 가져오기
                        new_lowest_price = _db.fetch_one(lowest_price_search_query, [grouping_product_id])

                        # 가격 변동 체크
                        if old_lowest_price and new_lowest_price and old_lowest_price['price'] != new_lowest_price['price']:
                            logger.info(f"가격 변동 감지: {title} - {old_lowest_price['price']} -> {new_lowest_price['price']}")

                            price_history_data = {
                                'productId': grouping_product_id,
                                'sellerId': seller_site_id,
                                'oldPrice': old_lowest_price['price'],
                                'newPrice': new_lowest_price['price'],
                                'priceDifference': new_lowest_price['price'] - old_lowest_price['price'],
                                'percentageChange': (new_lowest_price['price'] - old_lowest_price['price']) / old_lowest_price['price'] * 100 if old_lowest_price['price'] else 0,
                            }
                            _db.insert_data('vapesite.vape_price_history', price_history_data)
                            logger.info(f"가격 이력 저장 완료: {title} - {old_lowest_price['price']} -> {new_lowest_price['price']}")
                    else:
                        _db.update_data(
                            'vapesite.vape_price_comparisons',
                            {'originTitle': title},
                            'id = %s',
                            (price_comparison_id,)
                        )

                else:
                    comparison_id = _db.insert_data('vapesite.vape_price_comparisons', price_comparison_data)
                    logger.info(f"새 가격 비교 데이터 저장 완료: {title} - {new_price}")
                    price_history_data = {
                        'productId': grouping_product_id,
                        'sellerId': seller_site_id,
                        'oldPrice': 0,
                        'newPrice': new_price
                    }
                    _db.insert_data('vapesite.vape_price_history', price_history_data)
                    logger.info(f"신규 가격 이력 저장 완료: {title}")
            except Exception as e:
                logger.error(f"가격 비교 데이터 저장 중 오류 발생: {e}")
                logger.error(f"상품 데이터: {json.dumps(product, ensure_ascii=False, indent=2)}")
                exit()

    logger.info(f"--- 그룹 상세 ---")
    logger.info(f"그룹 수: {len(final_grouped_products)}")
