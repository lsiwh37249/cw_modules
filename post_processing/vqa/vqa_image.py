import json
import os
from typing import Dict, Any

def map_vqa_images_to_filenames(data):
    """VQA 이미지 선택을 실제 이미지 파일명으로 매핑"""
    
    # VQA 관련 필드들 (01~09)
    vqa_numbers = ["01", "02", "03", "04", "05", "06", "07", "08", "09"]
    
    print("=== VQA 이미지 매핑 결과 ===")
    
    for vqa_num in vqa_numbers:
        # VQA_image_XX에서 선택된 이미지 정보 추출
        image_key = f"VQA_image_{vqa_num}"
        
        if image_key in data and "data" in data[image_key]:
            image_data = data[image_key]["data"][0]
            
            # 선택된 이미지들의 value 배열에서 실제 이미지 파일명 추출
            selected_images = []
            if "value" in image_data:
                for img_item in image_data["value"]:
                    selected_images.append(img_item.get("value", ""))
            
            # importData_image_VQA_XX에서 실제 이미지 파일명 찾기
            actual_filenames = []
            for selected_img in selected_images:
                # "image_VQA_01" -> "01" 추출
                if selected_img.startswith("image_VQA_"):
                    img_num = selected_img.replace("image_VQA_", "")
                    import_key = f"importData_image_VQA_{img_num}"
                    
                    if import_key in data:
                        actual_filename = data[import_key]
                        actual_filenames.append(actual_filename)
                        print(f"VQA_{vqa_num}: {selected_img} -> {actual_filename}")
                    else:
                        print(f"VQA_{vqa_num}: {selected_img} -> 해당하는 importData를 찾을 수 없음")
                else:
                    print(f"VQA_{vqa_num}: {selected_img} -> 예상하지 못한 형식")
            
            print(f"VQA_{vqa_num} 선택된 이미지: {selected_images}")
            print(f"VQA_{vqa_num} 실제 파일명: {actual_filenames}")
            print("---")
        else:
            print(f"VQA_{vqa_num}: 데이터가 없음")
            print("---")
    
    return True

def find_vqa_image_files(data):
    """모든 VQA 이미지 파일명 찾기"""
    
    print("=== 모든 VQA 이미지 파일명 ===")
    
    for i in range(1, 10):  # 01~09
        key = f"importData_image_VQA_{i:02d}"
        if key in data:
            filename = data[key]
            print(f"{key}: {filename}")
        else:
            print(f"{key}: 없음")
    
    print("---")
    return True

def select_images(data):
    """VQA 데이터를 추출하여 템플릿에 추가"""
    
    # VQA 관련 필드들 (01~03)
    vqa_numbers = ["01", "02", "03"]
    
    # 각 VQA 번호별로 처리
    for vqa_num in vqa_numbers:
        # VQA_image_XX에서 선택된 이미지 정보 추출
        image_key = f"VQA_image_{vqa_num}"
        
        if image_key in data and "data" in data[image_key]:
            image_data = data[image_key]["data"][0]
            image_id = image_data.get("objectID", f"image_VQA_{vqa_num}")
            
            # 선택된 이미지들의 value 배열에서 실제 이미지 파일명 추출
            selected_images = []
            if "value" in image_data:
                for img_item in image_data["value"]:
                    selected_images.append(img_item.get("value", ""))
            
            print(f"VQA_{vqa_num}에서 선택된 이미지: {selected_images}")

    
    return selected_images



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
            for i, line in enumerate(f, start=1):
                line = line.strip()  # 개행 제거
                if not line:  # 빈 줄 건너뛰기
                    continue
                try:
                    data = json.loads(line)
                    print(f"[{i}] JSON 데이터 로드 완료")
                    print(f"데이터 키들: {list(data.keys())}")
                    print("---")
                except json.JSONDecodeError as e:
                    print(f"[{i}] JSON 파싱 오류: {e}")
        
                # 모든 VQA 이미지 파일명 출력
                find_vqa_image_files(data)
        
                # VQA 이미지 선택과 실제 파일명 매핑
                map_vqa_images_to_filenames(data)
        
        
    except FileNotFoundError:
        print(f"입력 파일을 찾을 수 없습니다: {input_path}")
    except Exception as e:
        print(f"오류 발생: {e}")



