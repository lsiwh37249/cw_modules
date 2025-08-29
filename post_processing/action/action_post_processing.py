import json
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
            return []  # 빈 배열로 초기화
        # 그 외 값은 빈 문자열로 처리
        else:
            return ""
    
    return _process_value(data)

def add_base(template: Dict[str, Any], data):
    # dataID(int), dataset_name(str), version(str), year(str), category(arr), subject(arr) 
    
    template['dataID'] = data['dataID']
    template['dataset_name'] = "example_dataset"
    template['version'] = "v1.0"
    template['year'] = "2025"
    template['category'] = []
    template['subject'] = []
    
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
    
def add_scene_annotation(template, data):
    """Scene 데이터를 추출하여 템플릿에 추가"""
    
    # scene 관련 필드들 (01~03)
    scene_numbers = ["01", "02", "03"]
    
    # 각 scene 번호별로 처리
    for scene_num in scene_numbers:
        # scene_XX에서 objectID 추출하여 scene_id에 사용
        scene_key = f"scene_{scene_num}"
        if scene_key in data and "data" in data[scene_key]:
            scene_data = data[scene_key]["data"][0]
            scene_id = scene_data.get("objectID", f"scene_dataId_{scene_num}")
        else:
            scene_id = f"scene_dataId_{scene_num}"
        
        # scene_description_XX에서 value 추출하여 description_scene_kr에 사용
        description_key = f"scene_description_{scene_num}"
        if description_key in data and "data" in data[description_key]:
            description_data = data[description_key]["data"][0]
            description_kr = description_data.get("value", "")
        else:
            description_kr = ""
        
        # scene 항목 생성
        scene_item = {
            "scene_id": scene_id,
            "description_scene_kr": description_kr,
            "description_scene_en": ""  # 영어 번역은 나중에 추가
        }
        
        template["scene_annotation"].append(scene_item)
    
    return template


def post_processing(data: Dict[str, Any]):
    # 원본 데이터 구조
    base_format_data = json.load(open('../data/format/VQA 데이터 포맷.txt', 'r', encoding='utf-8'))

    # 초기화
    template = initialize_template(base_format_data)

    # (공통)기본 데이터 추가 : dataID(int), dataset_name(str), version(str), year(str), category(arr), subject(arr) 
    first_template = add_base(template, data)

    # (공통)영상데이터 추가 : video(arr + dict)
    second_template = add_video(first_template, data)

    # (공통)클립데이터 추가 : clip(dict)
    third_template = add_clip(second_template, data)

    # scene_annotation 추가 : scene_annotation(arr + dict) 
    final_template = add_scene_annotation(third_template, data)

    # 파일로 저장
    return final_template


def post_processing_scene_only(data):
    """Scene 데이터만 후처리하는 함수"""
    template = {"scene_annotation": []}
    template = add_scene_annotation(template, data)
    return template

if __name__ == "__main__":
    # JSON 파일 로드
    input_path = "../data/json/26540_result_4b4edc2630.json"
    output_path = "../data/result/behavior_result.json"
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            first_line = f.read()
            data, _ = json.JSONDecoder().raw_decode(first_line)  # 첫 번째 JSON만 파싱
            print(data)
        
        # 전체 데이터 후처리 실행 (기본 정보 + 비디오 + 클립 + VQA)
        result = post_processing(data)
        
        # 결과 저장
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"Behavior 후처리 완료: {output_path}")
        print(f"총 {len(result['scene_annotation'])}개의 scene 항목이 처리되었습니다.")
        
    except FileNotFoundError:
        print(f"입력 파일을 찾을 수 없습니다: {input_path}")
    except Exception as e:
        print(f"오류 발생: {e}")



