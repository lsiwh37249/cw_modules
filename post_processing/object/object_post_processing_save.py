import os
import json
from typing import Any, Dict, List, Union

# 초기화 함수
def initialize_template(data: Dict[str, Any]):
    
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

def add_base(template: Dict[str, Any], data):
    # dataID(int), dataset_name(str), version(str), year(str), category(arr), subject(arr) 
    
    template['dataID'] = data['dataID']
    template['dataset_name'] = "example_dataset"
    template['version'] = "v1.0"
    template['year'] = "2025"
    template['category'] = [None]
    template['subject'] = [None]
    
    return template

def add_video(template: Dict[str, Any], data):
    clip_name = data.get('importData_video_file', 'unknown_video.mp4')
    
    # 확장자 제거 후 마지막 _숫자 부분 제거
    clip_name = clip_name.replace('.mp4', '')  # .mp4 제거
    if '_' in clip_name:
        parts = clip_name.split('_')
        # 마지막 부분이 숫자인지 확인하고 제거
        if parts[-1].isdigit():
            clip_name = '_'.join(parts[:-1])  # 마지막 숫자 부분 제거
    
    # video 정보 추가
    template['video'] = [
        {
            "id": "video_001",
            "width": "",
            "height": "",
            "file_name": f"{clip_name}.mp4"
        }
    ]
    
    return template

def add_clip(template: Dict[str, Any], data):
    clip_name = data.get('importData_video_file', 'unknown_video.mp4')

    template['clip'] = {
        "id": f"clip_{clip_name.split('_')[-1].split('.')[0]}",
        "file_name": clip_name,
        "length": "",  # 전체 영상 길이
        "width": None,
        "height": None,
        "format": "mp4",
        "ratio": None,
        "fps": ""
    }
    
    return template

def add_object_annotation(template: Dict[str, Any], data):
    # 객체 데이터 추출
    object_annotations = []
    frame_counter = 1  # frame 번호를 위한 카운터

    # object 데이터가 있는지 확인
    if "object" in data and "data" in data["object"]:
        object_data = data["object"]["data"]
        
        for obj in object_data:
            source_image = obj["SourceValue"]
            chain_id = obj["ChainId"]
            
            # ChainData에서 각 객체 정보 추출
            if "ChainData" in obj:
                for chain_item in obj["ChainData"]:
                    if "value" in chain_item:
                        value = chain_item["value"]
                        
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
                        
                        # 각 객체를 개별적으로 object_annotations에 추가
                        object_annotation = {
                            #"image_id": f"frame_{frame_counter:03d}",  # frame_001, frame_002, ...
                            "image_id": source_image,  # 실제 이미지 파일명 (예: I_Live_Alone_20250530_6_O_15.jpg)
                            "object_id": chain_item["objectID"],
                            "image_frame": "",
                            "object_name_kr": value.get("object_name", ""),  # 한글 이름
                            "object_name_en": "",  # 영어 이름 (현재 데이터에 없음)
                            "bbox": bbox
                        }
                        
                        object_annotations.append(object_annotation)
                        frame_counter += 1  # 다음 객체마다 번호 증가
    
    template['object_annotation'] = object_annotations
    return template

def post_processing(data: Dict[str, Any]):
    # 원본 데이터 구조
    base_format_data = json.load(open('../data/format/객체 데이터 포맷.txt', 'r', encoding='utf-8'))

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
        # 정보 데이터 추출
    with open('../data/json/26540_result_4b4edc2630.json', 'r', encoding='utf-8') as f:
        first_line = f.readline()
        data = json.loads(first_line)
        
    result = post_processing(data)
    
    os.makedirs('../data/result', exist_ok=True)

    with open('../data/result/result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

