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
    
def add_VQA_annotation(template, data):
    """VQA 데이터를 추출하여 템플릿에 추가"""
    
    # VQA 관련 필드들 (01~03)
    vqa_numbers = ["01", "02", "03"]
    
    # 각 VQA 번호별로 처리
    for vqa_num in vqa_numbers:
        # VQA_image_XX에서 objectID 추출하여 image_id에 사용
        image_key = f"VQA_image_{vqa_num}"
        
        if image_key in data and "data" in data[image_key]:
            image_data = data[image_key]["data"][0]
            image_id = image_data.get("objectID", f"image_VQA_{vqa_num}")
        else:
            image_id = f"image_VQA_{vqa_num}"
        
        # VQA_question_XX에서 objectID 추출하여 question_id에 사용
        question_key = f"VQA_question_{vqa_num}"
        if question_key in data and "data" in data[question_key]:
            question_data = data[question_key]["data"][0]
            question_id = question_data.get("objectID", f"question_dataId_{vqa_num}")
            question_kr_base = question_data.get("value", "")
        else:
            question_id = f"question_dataId_{vqa_num}"
            question_kr_base = ""
        
        # 선지들 추출 (VQA_question_XXY)
        choices = []
        for choice_num in range(1, 5):  # 1~4번 선지
            choice_key = f"VQA_question_{vqa_num}{choice_num}"
            print(f"DEBUG: Looking for choice_key: {choice_key}")
            if choice_key in data and "data" in data[choice_key]:
                choice_data = data[choice_key]["data"][0]
                choice_text = choice_data.get("value", "")
                choices.append(choice_text)
                print(f"DEBUG: Found choice: {choice_text}")
            else:
                print(f"DEBUG: Choice key {choice_key} not found or no data")
                
        # question_kr에 질문과 선지들을 모두 포함
        if choices:
            question_kr = f"{question_kr_base},{','.join(choices)}"
        else:
            question_kr = question_kr_base
    

        
        # VQA_answer_XX에서 objectID와 value 추출
        answer_key = f"VQA_answer_{vqa_num}"
        if answer_key in data and "data" in data[answer_key]:
            answer_data = data[answer_key]["data"][0]
            answer_id = answer_data.get("objectID", f"answer_dataId_{vqa_num}")
            answer_value = answer_data.get("value", [])
            if answer_value and len(answer_value) > 0:
                answer = int(answer_value[0].get("value", 1))
            else:
                answer = 1
        else:
            answer_id = f"answer_dataId_{vqa_num}"
            answer = 1
        
        # VQA 항목 생성
        vqa_item = {
            "image_id": image_id,
            "image_frame": "",  # 간단한 시간 프레임
            "question_id": question_id,
            "question_kr": question_kr,
            "question_en": "",
            "answer_id": answer_id,
            "answer": answer
        }
        
        template["VQA_annotation"].append(vqa_item)
    
    return template


def post_processing(data: Dict[str, Any]):
    # 원본 데이터 구조
    base_format_data = json.load(open('C:/code/data/format/VQA 데이터 포맷.txt', 'r', encoding='utf-8'))

    # 초기화
    template = initialize_template(base_format_data)

    # (공통)기본 데이터 추가 : dataID(int), dataset_name(str), version(str), year(str), category(arr), subject(arr) 
    first_template = add_base(template, data)

    # (공통)영상데이터 추가 : video(arr + dict)
    second_template = add_video(first_template, data)

    # (공통)클립데이터 추가 : clip(dict)
    third_template = add_clip(second_template, data)

    # VQA_annotation 추가 : VQA_annotation(arr + dict) 
    final_template = add_VQA_annotation(third_template, data)

    # 파일로 저장
    return final_template


def post_processing_vqa_only(data):
    """VQA 데이터만 후처리하는 함수"""
    template = {"VQA_annotation": []}
    template = add_VQA_annotation(template, data)
    return template

if __name__ == "__main__":
    # JSON 파일 로드
    input_path = "C:/code/data/json/26540_result_4b4edc2630.json"
    output_path = "C:/code/data/result/vqa_result.json"
    
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
        
        print(f"VQA 후처리 완료: {output_path}")
        print(f"총 {len(result['VQA_annotation'])}개의 VQA 항목이 처리되었습니다.")
        
    except FileNotFoundError:
        print(f"입력 파일을 찾을 수 없습니다: {input_path}")
    except Exception as e:
        print(f"오류 발생: {e}")



