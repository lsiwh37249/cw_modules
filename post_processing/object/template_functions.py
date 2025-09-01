from typing import Any, Dict

def add_base(template: Dict[str, Any], data):
    """기본 데이터 추가"""
    template['dataID'] = data['dataID']
    template['dataset_name'] = "example_dataset"
    template['version'] = "v1.0"
    template['year'] = "2025"
    template['category'] = [None]
    template['subject'] = [None]
    
    return template

def add_video(template: Dict[str, Any], data):
    """영상 데이터 추가"""
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
    """클립 데이터 추가"""
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
