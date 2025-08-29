import json
import os
import glob
from pathlib import Path


def remove_newlines_from_scene_description(data):
    """scene_description의 \n 문자를 제거합니다."""
    if 'scence_description' in data and 'data' in data['scence_description']:
        for item in data['scence_description']['data']:
            if 'value' in item:
                item['value'] = item['value'].replace('\n', ' ')
        return data


def print_data_id(data):
    """dataID를 출력합니다."""
    if 'dataID' in data:
        print(f"  dataID: {data['dataID']}")


def check_newlines_in_scene_description(data):
    """scene_description의 value에 개행문자가 있는지 확인합니다."""
    if 'scence_description' in data and 'data' in data['scence_description']:
        for item in data['scence_description']['data']:
            if 'value' in item:
                has_newlines = '\n' in item['value']
                newline_count = item['value'].count('\n')
                print(f"    scene_description value에 개행문자: {'있음' if has_newlines else '없음'}")
                if has_newlines:
                    print(f"      개행문자 개수: {newline_count}개")
                return  has_newlines
    return False


def main():
    """
    메인 함수
    """
    # 현재 작업 디렉토리 기준으로 data 폴더들 처리
    data_dirs = [
        "C:/code/data/cleansing_data",

    ]
    
    for data_dir in data_dirs:
        if os.path.exists(data_dir):
            print(f"처리 중: {data_dir}")
            
            # JSON 파일 찾기
            json_files = glob.glob(os.path.join(data_dir, "**/*.json"), recursive=True)
            
            for file_path in json_files:
                try:
                    print(f"  📁 {os.path.basename(file_path)}")
                    
                    # 파일 읽기
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 한 줄씩 처리
                    lines = content.strip().split('\n')
                    processed_lines = []
                    
                    for line in lines:
                        if line.strip():
                            try:
                                data = json.loads(line)
                                
                                # dataID 출력
                                print_data_id(data)
                                
                                # scene_description에 개행문자가 있는지 확인
                                check_newlines_in_scene_description(data)
                                
                                # scene_description의 \n 제거
                                data = remove_newlines_from_scene_description(data)
                                
                                processed_lines.append(json.dumps(data, ensure_ascii=False))
                                
                            except json.JSONDecodeError:
                                processed_lines.append(line)
                    
                    # 수정된 내용을 파일에 쓰기
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(processed_lines))
                        
                except Exception as e:
                    print(f"  오류: {e}")
        else:
            print(f"디렉토리가 존재하지 않음: {data_dir}")


if __name__ == "__main__":
    main()
