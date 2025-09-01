import os
import json
from typing import Any, Dict, List, Union

# 분리된 모듈들 import
from object_utils import initialize_template, filter_chain_data, process_valid_chain_items
from template_functions import add_base, add_video, add_clip
from logging_config import setup_logging, get_logger

# 로깅 설정
logger = get_logger()

def add_object_annotation(template: Dict[str, Any], data):
    # 객체 데이터 추출
    object_annotations = []
    frame_counter = 1  # frame 번호를 위한 카운터

    # object 데이터가 있는지 확인
    if "object" in data and "data" in data["object"]:
        object_data = data["object"]["data"]
        logger.info(f"전체 SourceValue 처리 시작 (총 {len(object_data)}개)")
        
        for i, obj in enumerate(object_data):
            source_image = obj["SourceValue"]
            chain_id = obj["ChainId"]
            
            logger.info(f"SourceValue {i+1} 처리: {source_image} (ChainID: {chain_id})")
            
            # ChainData에서 각 객체 정보 추출 및 필터링
            if "ChainData" in obj:
                logger.debug(f"ChainData 개수: {len(obj['ChainData'])}")
                
                # 필터링 함수 호출
                valid_chain_items, additional_work_impossible_count = filter_chain_data(obj["ChainData"])
                
                # 3. 추가 작업 불가 객체가 5개 이상이면 해당 SourceValue 전체 삭제
                if additional_work_impossible_count >= 5:
                    logger.warning(f"추가 작업 불가 객체가 {additional_work_impossible_count}개로 5개 이상이므로 이 SourceValue 전체 삭제")
                    continue  # 이 SourceValue는 건너뛰기
                else:
                    logger.info(f"추가 작업 불가 객체가 {additional_work_impossible_count}개로 5개 미만이므로 처리 진행")
                
                # 4. 5개 이하면 추가 작업 불가 객체만 제외하고 나머지 처리
                new_annotations, frame_counter = process_valid_chain_items(
                    valid_chain_items, source_image, frame_counter
                )
                object_annotations.extend(new_annotations)
                logger.info(f"이 SourceValue에서 {len(new_annotations)}개의 annotation 생성됨")
            else:
                logger.warning("ChainData가 없음")
    
    logger.info(f"최종 결과 - 총 생성된 annotation 수: {len(object_annotations)}")
    
    template['object_annotation'] = object_annotations
    return template

def post_processing(data: Dict[str, Any]):
    # 원본 데이터 구조
    base_format_data = json.load(open('../../data/format/객체 데이터 포맷.txt', 'r', encoding='utf-8'))

    # 초기화
    null_template = initialize_template(base_format_data)
    
    # (공통)기본 데이터 추가 : dataID(int), dataset_name(str), version(str), year(str), category(arr), subject(arr) 
    first_template = add_base(null_template, data)

    # (공통)영상데이터 추가 : video(arr + dict)
    second_template = add_video(first_template, data)

    # (공통)클립데이터 추가 : clip(dict)
    third_template = add_clip(second_template, data)

    # VQA_annotation 추가 : VQA_annotation(arr + dict) 
    final_template = add_object_annotation(third_template, data)

    # 파일로 저장
    return final_template

if __name__ == "__main__":
    # 로깅 설정
    setup_logging()
    
    # 정보 데이터 추출
    logger.info("파일 읽기 시작")
    results = []
    
    try:
        with open('../../data/raw_data/20250901/26606_result_d2a27e83d4.json', 'r', encoding='utf-8') as f:
            line_count = 0
            for line in f:
                line_count += 1
                line = line.strip()
                if not line:  # 빈 줄 건너뛰기
                    continue
                    
                logger.info(f"{line_count}번째 라인 처리 시작 (라인 길이: {len(line)})")
                
                try:
                    data = json.loads(line)
                    logger.debug(f"데이터 로드 완료 - dataID: {data.get('dataID', 'N/A')}")
                    logger.debug(f"데이터 키들: {list(data.keys())}")
                    
                    # object 데이터 확인
                    if "object" in data:
                        logger.debug(f"object 키 존재: {list(data['object'].keys())}")
                        if "data" in data["object"]:
                            object_data = data["object"]["data"]
                            logger.debug(f"object data 개수: {len(object_data)}")
                            if object_data:
                                logger.debug(f"첫 번째 object의 키들: {list(object_data[0].keys())}")
                            else:
                                logger.warning("object data가 빈 리스트")
                        else:
                            logger.warning("object.data가 없음")
                    else:
                        logger.warning("object 키가 없음")
                    
                    logger.info("post_processing 시작")
                    result = post_processing(data)
                    results.append(result)
                    logger.info("post_processing 완료")
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON 파싱 오류 (라인 {line_count}): {e}")
                    continue
                except Exception as e:
                    logger.error(f"처리 오류 (라인 {line_count}): {e}")
                    import traceback
                    logger.error(f"상세 오류: {traceback.format_exc()}")
                    continue
                    
    except Exception as e:
        logger.error(f"파일 읽기 오류: {e}")
        import traceback
        logger.error(f"상세 오류: {traceback.format_exc()}")
        exit(1)
    
    logger.info(f"전체 처리 완료 - 총 처리된 데이터 수: {len(results)}")
    
    logger.info("결과 디렉토리 생성")
    os.makedirs('../../data/result', exist_ok=True)
    logger.info("결과 디렉토리 생성 완료")

    logger.info("결과 파일 저장")
    with open('../../data/result/result.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info("결과 파일 저장 완료")

