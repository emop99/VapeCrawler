import json
import logging
import re
import os
from collections import defaultdict
from module.MariaDBConnector import MariaDBConnector

"""
VapeSort.py - 베이프 상품 정보 정렬 및 그룹화 스크립트
"""

# DB 연결
_db = None
# 브랜드 목록 캐시 (메모리 캐싱)
_brand_cache = None

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('log/vape_sort.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('vape_sort')


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
    common_words_to_remove = ["정품", "새상품", "입호흡", "폐호흡", "액상샵", "특가", "할인", "rs니코틴", "s니코틴", "★", "blvk", "저농도"]
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


def extract_product_features(title, product_type, url):
    """`
    정규화된 상품명에서 브랜드, 제품명, 용량, 기타 세부정보를 추출합니다.
    """
    normalized_title = normalize_title_text(title)

    brand = None
    brand_id = 1
    details = []  # 기타 세부 정보

    # 데이터베이스에서 브랜드 목록 가져오기
    known_brands = get_vape_brands_from_db()

    # 브랜드 추출 (가장 긴 브랜드 이름부터 매칭 시도)
    # 브랜드 이름이 상품명 중간에 있을 수도 있으므로, 더 정교한 로직이 필요할 수 있습니다.
    # 여기서는 간단히 앞에서부터 매칭합니다.
    temp_title_for_brand = normalized_title  # 원본 정규화 제목 복사
    for b_name, brand_info in sorted(known_brands.items(), key=lambda x: len(x[0]), reverse=True):
        if temp_title_for_brand.startswith(b_name.lower()):
            brand = b_name
            brand_id = brand_info['id']
            temp_title_for_brand = temp_title_for_brand.replace(b_name.lower(), "").strip()
            break

    # 제품 코어명 (브랜드와 용량을 제외한 부분)
    # 좀 더 정교한 제품명 추출 로직이 필요할 수 있음 (예: 알려진 제품 라인업)
    product_name_core = re.sub(r'\s+', ' ', temp_title_for_brand).strip()  # 연속 공백 정리

    # 최종 식별키 생성
    # 브랜드, 제품 코어명, 용량이 모두 있어야 유효한 키로 간주 (엄격한 매칭)
    # 경우에 따라 용량 없이 (브랜드, 제품 코어명)만으로도 그룹핑할 수 있음 (느슨한 매칭)

    # 기본적인 정규화 (공백, 특수문자 등)
    if product_name_core:
        product_name_core = product_name_core.replace("  ", " ").strip()
        product_name_core = product_name_core.replace("액상", "").strip()  # '액상' 단어 제거

    # 기본 키: 브랜드, 제품 코어명, 용량, 상품 유형 (입호흡/폐호흡)
    # 이 키를 사용하여 그룹핑합니다.
    # 브랜드가 None일 경우 "알수없음" 등으로 처리 가능
    # 제품 코어명이 비어있으면 그룹핑하기 어려움

    # 정제된 제품명 생성: 추출된 요소들을 조합 (예: 펠릭스 라임라임)
    # 용량이 이름에 포함된 경우가 많으므로, 추출 후 재조합 시 주의
    refined_name_parts = []
    if brand:
        temp_name = product_name_core.replace(brand.lower(), "").strip()
        refined_name_parts.append(temp_name)
    else:
        logger.warning(f"알려진 브랜드가 없습니다. {normalized_title} {product_name_core} {url}")
        if not brand and " " in product_name_core:
            brand = product_name_core.split(" ")[0]
            product_name_core = product_name_core[len(brand):].strip()
        refined_name_parts.append(product_name_core)

    # 최종 제품 코어명 정제
    product_name_core_final = " ".join(part for part in refined_name_parts if part).strip()
    product_name_core_final = re.sub(r'\s+', ' ', product_name_core_final).strip()

    if brand and product_name_core_final:
        # 기본 그룹핑 키: (브랜드 idx, 브랜드명, 제품명, 제품 타입)
        grouping_key = (
            brand_id,
            brand.lower(),
            product_name_core_final.lower(),
            product_type.lower()  # 입호흡/폐호흡 구분
        )
        return grouping_key, tuple(sorted(list(set(details))))  # details는 현재 거의 사용 안됨

    return None, tuple(sorted(list(set(details))))  # 필수 정보 부족 시 None 반환


# --- 2단계: 파일 로드 및 상품 데이터 통합 ---

def load_and_integrate_products(file_paths):
    """여러 JSON 파일에서 상품 정보를 로드하고 통합합니다."""
    all_products_info = []
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
                            all_products_info.append(product)
        except FileNotFoundError:
            logger.error(f"오류: 파일을 찾을 수 없습니다 - {file_path}")
        except json.JSONDecodeError:
            logger.error(f"오류: JSON 디코딩 실패 - {file_path}")
        except Exception as e:
            logger.error(f"파일 처리 중 오류 발생 ({file_path}): {e}")
    return all_products_info


# --- 3단계: 상품 그룹핑 ---

def group_products(integrated_products):
    """통합된 상품 리스트를 그룹핑합니다."""
    grouped_by_key = defaultdict(list)

    for i, product_data in enumerate(integrated_products):
        title = product_data.get("title", "")
        product_type = product_data.get("product_type", "알수없음")  # 입호흡/폐호흡
        url = product_data.get("url", "")

        primary_key, details = extract_product_features(title, product_type, url)

        # 원본 정보와 함께 저장
        full_product_info = {
            "original_title": title,
            "normalized_title_for_feature_extraction": normalize_title_text(title),  # 디버깅용
            "primary_key": primary_key,
            "details_from_extraction": details,  # 디버깅용
            "price": product_data.get("price"),
            "url": url,
            "image_url": product_data.get("image_url"),
            "source_file": product_data.get("source_file"),
            "product_type": product_type
        }

        if primary_key:
            logger.info(f"상품: {title} -> 키: {primary_key}")
            # 동일 상품 판단 기준: primary_key (브랜드, 제품명, 용량, 타입)
            # 추가적으로 details (남은 문자열)를 비교하여 더 엄격하게 그룹핑 가능
            # 여기서는 primary_key가 동일하면 같은 상품으로 간주
            grouping_final_key = primary_key
            grouped_by_key[grouping_final_key].append(full_product_info)
        else:
            logger.info(f"상품: {title} -> 키 생성 실패 (필수 정보 부족) {url}")
            # 키 생성 실패 상품은 별도 그룹 또는 처리 로직 추가 가능
            grouped_by_key[("키_생성_실패", title)].append(full_product_info)

    return grouped_by_key


# --- 실행 ---
if __name__ == "__main__":
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

    # 데이터베이스 연결
    _db = MariaDBConnector()
    if not _db.connect():
        logger.error("데이터베이스 연결 실패")
        exit()

    all_integrated_products = load_and_integrate_products(existing_file_paths)

    if not all_integrated_products:
        logger.error(f"로드된 상품이 없습니다. JSON 파일 내용이나 구조를 확인해주세요.")
        exit()

    logger.info(f"총 {len(all_integrated_products)}개의 상품 정보를 통합했습니다.")

    final_grouped_products = group_products(all_integrated_products)

    logger.info("--- 최종 그룹핑 결과 ---")
    group_count = 0
    single_item_group_count = 0
    key_make_fail_count = 0
    product_name = ""
    seller_site_list = get_vape_seller_from_db()
    product_category_list = get_vape_product_category_from_db()
    for key, products_in_group in final_grouped_products.items():
        if key[0] == "키_생성_실패":
            key_make_fail_count += 1
            continue

        # 키 생성된 상품 vape_products 테이블에 적재 처리
        try:
            # 그룹 내 첫 번째 상품만 저장 (중복 방지)
            product_name = products_in_group[0]['primary_key'][2]
            company_id = int(products_in_group[0]['primary_key'][0])
            product_category_id = product_category_list[products_in_group[0]['product_type']]['id']

            # 데이터베이스에 저장할 데이터 준비
            product_data = {
                'companyId': company_id,
                'productCategoryId': product_category_id,
                'name': product_name,
                'imageUrl': products_in_group[0]['image_url']
            }

            # 데이터베이스에 저장
            product_id = _db.insert_data('vapesite.vape_products', product_data)
        except Exception as e:
            error_str = str(e)

            # Duplicate entry 오류인 경우 해당 상품 정보를 select
            if "Duplicate entry" in error_str:
                logger.info(f"중복 상품 감지: {product_name}. 기존 상품 정보를 조회합니다.")
                try:
                    # 회사 ID와 상품명으로 기존 상품 조회
                    query = "SELECT id, name FROM vapesite.vape_products WHERE companyId = %s AND name = %s"
                    product = _db.fetch_one(query, (company_id, product_name))

                    if product:
                        logger.info(f"기존 상품 정보 조회 성공: ID={product['id']}, 이름={product['name']}")
                        product_id = product['id']
                    else:
                        logger.error(f"중복 오류가 발생했으나 상품을 찾을 수 없습니다: {product_name}")
                        exit()
                except Exception as select_error:
                    logger.error(f"기존 상품 정보 조회 중 오류 발생: {select_error}")
                    exit()
            else:
                # 다른 종류의 오류인 경우 프로그램 종료
                logger.error(f"상품 저장 중 오류 발생: {e}")
                exit()

        # vape_price_comparisons 테이블 적재 처리
        for product in products_in_group:
            try:
                # 판매 사이트 정보 가져오기
                seller_site_id = seller_site_list[product['source_file']]['id']
                if not seller_site_id:
                    logger.error(f"검색된 판매 사이트 정보가 없습니다. {product['source_file']}")
                    continue

                # 가격 비교 테이블에 저장할 데이터 준비
                price_comparison_data = {
                    'productId': product_id,
                    'sellerId': seller_site_id,
                    'sellerUrl': product['url'],
                    'price': product['price']
                }

                # 이미 존재하는지 확인
                query = "SELECT price FROM vapesite.vape_price_comparisons WHERE productId = %s AND sellerId = %s ORDER BY updatedAt DESC LIMIT 1"
                existing_price = _db.fetch_one(query, (product_id, seller_site_id))

                if existing_price:
                    # 기존 데이터가 있는 경우 가격 비교
                    old_price = existing_price['price']
                    new_price = product['price']

                    if old_price != new_price:
                        # 가격이 변경된 경우 업데이트
                        _db.update_data(
                            'vapesite.vape_price_comparisons',
                            {'price': new_price, 'sellerUrl': product['url']},
                            'productId = %s AND sellerId = %s',
                            (product_id, seller_site_id)
                        )
                        logger.info(f"가격 변동 감지: {product['original_title']} - {old_price} -> {new_price}")

                        # 가격 변동 이력 저장
                        price_history_data = {
                            'productId': product_id,
                            'sellerId': seller_site_id,
                            'oldPrice': old_price,
                            'newPrice': new_price,
                            'priceDifference': new_price - old_price,
                            'percentageChange': (new_price - old_price) / old_price * 100,
                        }
                        try:
                            _db.insert_data('vapesite.vape_price_history', price_history_data)
                        except Exception as e:
                            error_str = str(e)

                            # Duplicate entry 오류인 경우 해당 상품 정보를 select
                            if "Duplicate entry" in error_str:
                                continue
                            else:
                                raise e

                        logger.info(f"가격 변동 이력 저장 완료: {product['original_title']}")
                else:
                    # 새로운 데이터 삽입
                    comparison_id = _db.insert_data('vapesite.vape_price_comparisons', price_comparison_data)
                    logger.info(f"새 가격 비교 데이터 저장 완료: {product['original_title']} - {product['price']}")

                    # 신규 등록 이력 저장
                    price_history_data = {
                        'productId': product_id,
                        'sellerId': seller_site_id,
                        'oldPrice': 0,  # 신규 등록이므로 이전 가격은 0으로 설정
                        'newPrice': product['price']
                    }
                    _db.insert_data('vapesite.vape_price_history', price_history_data)
                    logger.info(f"신규 가격 이력 저장 완료: {product['original_title']}")

            except Exception as e:
                logger.error(f"가격 비교 데이터 처리 중 오류 발생: {e}")
                exit()

        if len(products_in_group) > 1:  # 2개 이상 같은 상품으로 판단된 경우만 출력
            group_count += 1
            logger.info(f"그룹 {group_count} (식별키: {key}) - 총 {len(products_in_group)}개 상품")
            for product in products_in_group:
                logger.info(f"  - {product['original_title']} (가격: {product['price']}, 출처: {product['source_file']}, URL: {product['url']}), IMG: {product['image_url']}")
        else:
            single_item_group_count += 1

    logger.info(f"--- 요약 ---")
    logger.info(f"총 {group_count}개의 그룹이 생성되었습니다 (2개 이상 동일 상품).")
    logger.info(f"총 {single_item_group_count}개의 상품이 단독으로 분류되었습니다.")
    logger.info(f"총 {key_make_fail_count}개의 상품이 키 생성에 실패하였습니다.")

    logger.info(f"--- final_grouped_products 상세 ---")
    logger.info(f"그룹 수: {len(final_grouped_products)}")
    logger.info(f"그룹 키 목록:")
    for key in final_grouped_products.keys():
        logger.info(f"- {key}: {len(final_grouped_products[key])}개 상품")
