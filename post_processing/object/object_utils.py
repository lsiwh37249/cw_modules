import json
from typing import Any, Dict, List, Union
from logging_config import get_logger

logger = get_logger()

def initialize_template(data: Dict[str, Any]):
    """템플릿 초기화 함수"""
    def _process_value(value: Any) -> Any:
        # 딕셔너리 처리
        if isinstance(value, dict):
            return {k: _process_value(v) for k, v in value.items()}
        # 리스트 처리   
        elif isinstance(value, list):
            return [_process_value(item) for item in value]
        # 그 외 값은 null로 처리
        else:
            return None
    
    return _process_value(data)

def find_source_values(data):
    """데이터에서 작업 가능한 이미지의 SourceValue만 추출"""
    if "object" in data and "data" in data["object"]:
        object_data = data["object"]["data"]
        
        for obj in object_data:
            if "SourceValue" in obj:
                source_image = obj["SourceValue"]
                
                # ChainData에서 작업 가능한 이미지인지 확인
                if "ChainData" in obj:
                    is_workable = False
                    for chain_item in obj["ChainData"]:
                        if "value" in chain_item and "extra" in chain_item["value"]:
                            extra = chain_item["value"]["extra"]
                            
                            # extra.label에 "작업 불가 이미지"가 포함되어 있으면 제외
                            if "label" in extra and "작업 불가 이미지" in extra["label"]:
                                is_workable = False
                                break
                            # extra.value가 "object"인 경우 작업 가능
                            elif extra.get("value") == "object":
                                is_workable = True
                    
                    # 작업 가능한 이미지만 로그
                    if is_workable:
                        logger.info(f"작업 가능한 이미지: {source_image}")

def filter_chain_data(chain_data):
    """
    ChainData를 필터링하는 함수
    - 작업제외이미지 제외
    - 추가 작업 불가 객체 카운트
    """
    additional_work_impossible_count = 0
    valid_chain_items = []
    excluded_items = []
    additional_work_impossible_items = []
    
    logger.info(f"ChainData 필터링 시작 (총 {len(chain_data)}개 아이템)")
    
    for i, chain_item in enumerate(chain_data):
        logger.debug(f"아이템 {i+1} 분석 시작")
        
        if "value" in chain_item:
            value = chain_item["value"]
            object_id = chain_item.get("objectID", "unknown")
            object_name = value.get("object_name", "")
            
            logger.debug(f"ObjectID: {object_id}, Object Name: {object_name}")
            
            # 1. 작업제외이미지 체크
            is_excluded = False
            if "extra" in value and "label" in value["extra"]:
                label = value["extra"]["label"]
                logger.debug(f"Extra Label: {label}")
                if "작업제외이미지" in label:
                    is_excluded = True
                    logger.warning(f"작업제외이미지로 판별됨 - ObjectID: {object_id}")
                    excluded_items.append({
                        "objectID": object_id,
                        "object_name": object_name,
                        "reason": "작업제외이미지",
                        "label": label
                    })
            else:
                logger.debug("Extra Label: 없음")
            
            # 작업제외이미지가 아닌 경우만 처리
            if not is_excluded:
                # 2. 추가 작업 불가 객체 카운트
                if "추가 작업 불가" in object_name:
                    additional_work_impossible_count += 1
                    logger.warning(f"추가 작업 불가 객체로 판별됨 - ObjectID: {object_id}")
                    additional_work_impossible_items.append({
                        "objectID": object_id,
                        "object_name": object_name
                    })
                else:
                    logger.debug(f"정상 객체로 판별됨 - ObjectID: {object_id}")
                
                valid_chain_items.append(chain_item)
        else:
            logger.error(f"value 필드가 없음 - 아이템 {i+1}")
    
    logger.info(f"필터링 결과 - 총: {len(chain_data)}, 제외: {len(excluded_items)}, 추가작업불가: {additional_work_impossible_count}, 유효: {len(valid_chain_items)}")
    
    if excluded_items:
        logger.info("작업제외이미지 목록:")
        for item in excluded_items:
            logger.info(f"  ObjectID: {item['objectID']}, Name: {item['object_name']}, Label: {item['label']}")
    
    if additional_work_impossible_items:
        logger.info("추가 작업 불가 객체 목록:")
        for item in additional_work_impossible_items:
            logger.info(f"  ObjectID: {item['objectID']}, Name: {item['object_name']}")
    
    return valid_chain_items, additional_work_impossible_count

def process_valid_chain_items(valid_chain_items, source_image, frame_counter):
    """
    유효한 chain_items를 처리하여 object_annotations 생성
    """
    object_annotations = []
    current_frame_counter = frame_counter
    processed_count = 0
    skipped_count = 0
    
    logger.info(f"유효한 chain_items 처리 시작 (총 {len(valid_chain_items)}개)")
    
    for i, chain_item in enumerate(valid_chain_items):
        value = chain_item["value"]
        object_name = value.get("object_name", "")
        object_id = chain_item["objectID"]
        
        logger.debug(f"아이템 {i+1}: ObjectID={object_id}, Name='{object_name}'")
        
        # 추가 작업 불가 객체는 제외
        if "추가 작업 불가" in object_name:
            logger.warning(f"추가 작업 불가 객체로 제외됨 - ObjectID: {object_id}")
            skipped_count += 1
            continue
        
        # 바운딩 박스 정보 - JSON에 이미 있는 width, height 사용
        bbox = []
        if "coords" in value:
            coords = value["coords"]
            bbox = [
                coords["tl"]["x"],  # top-left x
                coords["tl"]["y"],  # top-left y
                value["object"]["width"],  # 이미 계산된 width
                value["object"]["height"]   # 이미 계산된 height
            ]
            logger.debug(f"바운딩 박스 생성: {bbox}")
        else:
            logger.warning(f"coords 정보 없음 - ObjectID: {object_id}")
        
        # 각 객체를 개별적으로 object_annotations에 추가
        object_annotation = {
            "image_id": source_image,  # 실제 이미지 파일명
            "object_id": chain_item["objectID"],
            "image_frame": "",
            "object_name_kr": object_name,  # 한글 이름
            "object_name_en": "",  # 영어 이름 (현재 데이터에 없음)
            "bbox": bbox
        }
        
        object_annotations.append(object_annotation)
        current_frame_counter += 1  # 다음 객체마다 번호 증가
        processed_count += 1
        logger.debug(f"annotation 생성 완료 - ObjectID: {object_id}")
    
    logger.info(f"처리 결과 - 처리: {processed_count}개, 제외: {skipped_count}개, 생성: {len(object_annotations)}개")
    
    return object_annotations, current_frame_counter
