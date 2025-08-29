import cv2
import random
from pathlib import Path
import json
import re
import shutil

from pathlib import Path
from video_llm_RnD import (
    setup_gemini_api,
    get_images_from_folder,
    encode_image,
    analyze_images_with_gemini,
    transform2,
)

def extract_frames_from_video(video_path, output_dir, num_frames=45):
    # 비디오 캡처 객체 생성
    cap = cv2.VideoCapture(video_path)
    
    # 비디오 정보 가져오기
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = frame_count / fps
    
    print(f"비디오 정보: {frame_count} 프레임, {fps:.2f} FPS, {duration_sec:.2f}초")
    
    # 2초 간격으로 프레임 추출
    frame_interval = int(fps * 2)  # 2초 = fps * 2
    saved_frames = []
    video_stem = Path(video_path).stem
    
    print(f"프레임 추출 시작: 2초 간격, 추출 간격: {frame_interval} 프레임")
    
    frame_idx = 0
    idx = 0
    
    while frame_idx < frame_count and idx < num_frames:
        # 현재 프레임 위치를 frame_idx로 설정
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        success, frame = cap.read()
        
        if not success:
            print(f"❌ 프레임 읽기 실패 (#{idx+1})")
            frame_idx += frame_interval
            continue

        # 프레임 파일명 생성 및 저장
        frame_filename = f"{video_stem}_frame_{idx+1:02}.jpg"
        filepath = output_dir / frame_filename

        # 프레임 저장
        success = cv2.imwrite(str(filepath), frame)
        
        if success:
            # 프레임 파일명 리스트에 추가
            saved_frames.append(frame_filename)
            print(f"✅ 저장 완료: {filepath.name} (시간: {frame_idx/fps:.1f}초)")
        else:
            print(f"⚠️ 저장 실패: {filepath.resolve()}")
        
        idx += 1
        frame_idx += frame_interval
    
    # 비디오 캡처 객체 해제
    cap.release()
    
    print(f"프레임 추출 완료: {len(saved_frames)}개 저장됨")
    return saved_frames

def extract_45_frames_from_video(video_path, output_dir, num_frames=45):
    # 비디오 캡처 객체 생성
    cap = cv2.VideoCapture(video_path)
    
    # 비디오 정보 가져오기
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = frame_count / fps
    
    print(f"비디오 정보: {frame_count} 프레임, {fps:.2f} FPS, {duration_sec:.2f}초")
    
    # 프레임 추출 간격 계산
    step = max(1, int(frame_count / num_frames))
    saved_frames = []
    video_stem = Path(video_path).stem
    
    print(f"프레임 추출 시작: {num_frames}개, 간격: {step} 프레임")
    
    for idx, frame_idx in enumerate(range(0, frame_count, step)):
        if idx >= num_frames:
            break
        
        # 현재 프레임 위치를 frame_idx 로 설정
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        success, frame = cap.read()
        
        if not success:
            print(f"❌ 프레임 읽기 실패 (#{idx+1})")
            continue

        # 프레임 파일명 생성 및 저장
        frame_filename = f"{video_stem}_frame_{idx+1:02}.jpg"
        filepath = output_dir / frame_filename

        # 프레임 저장
        success = cv2.imwrite(str(filepath), frame)
        
        if success:
            # 프레임 파일명 리스트에 추가
            saved_frames.append(frame_filename)
            print(f"✅ 저장 완료: {filepath.name}")
        else:
            print(f"⚠️ 저장 실패: {filepath.resolve()}")
    
    # 비디오 캡처 객체 해제
    cap.release()
    
    print(f"프레임 추출 완료: {len(saved_frames)}개 저장됨")
    return saved_frames    

def process_images_and_create_folders(saved_frames, output_dir, output_dir_vo, video_stem):
    """
    이미지 처리 및 폴더 생성 함수
    
    Args:
        saved_frames (list): 저장된 프레임 파일명 리스트
        output_dir (Path): 프레임이 저장된 디렉토리
        output_dir_vo (Path): 최종 출력 디렉토리
        video_stem (str): 비디오 파일명 (확장자 제외)
        
    Returns:
        tuple: (image_object_filenames, image_V_map)
    """
    # 저장할 폴더 경로
    #image_object_dir = output_dir_vo / "image_object"
    #mage_V_dir = output_dir_vo / "image_VQA"
    image_object_dir = output_dir_vo
    image_V_dir = output_dir_vo
    # 폴더 생성
    image_object_dir.mkdir(exist_ok=True)
    print(f"✅ image_object 폴더 생성: {image_object_dir}")

    image_V_dir.mkdir(exist_ok=True)
    print(f"✅ image_VQA 폴더 생성: {image_V_dir}")

    # save_frame에서 순서를 고려한 12개 추출
    # 전체 프레임을 고르게 분포시켜서 12개 선택 (앞, 중간, 뒤 프레임 모두 포함)
    if len(saved_frames) >= 12:
        # 12개를 고르게 분포시켜 선택
        step = len(saved_frames) // 12
        selected_indices = [i * step for i in range(12)]
        # 마지막 프레임이 빠질 수 있으므로 마지막 인덱스 조정
        if selected_indices[-1] >= len(saved_frames):
            selected_indices[-1] = len(saved_frames) - 1
        selected_12 = [saved_frames[i] for i in selected_indices]
    else:
        # 프레임이 12개 미만인 경우 모두 선택
        selected_12 = saved_frames
    
    image_object_filenames = [f"{video_stem}_O_{i+1}.jpg" for i in range(len(selected_12))]

    # 선택된 12장을 image_object 폴더에 복사
    for src_name, dst_name in zip(selected_12, image_object_filenames):
        src_path = output_dir / src_name
        dst_path = image_object_dir / dst_name
        shutil.copy(src_path, dst_path)
        print(f"✅ 복사 완료: {src_name} → {dst_name}")

    # save_frame에서 순서를 고려한 9개 추출
    # 전체 프레임을 고르게 분포시켜서 9개 선택 (앞, 중간, 뒤 프레임 모두 포함)
    if len(saved_frames) >= 9:
        # 9개를 고르게 분포시켜 선택
        step = len(saved_frames) // 9
        selected_indices = [i * step for i in range(9)]
        # 마지막 프레임이 빠질 수 있으므로 마지막 인덱스 조정
        if selected_indices[-1] >= len(saved_frames):
            selected_indices[-1] = len(saved_frames) - 1
        selected_9 = [saved_frames[i] for i in selected_indices]
    else:
        # 9개 미만인 경우 모두 선택
        selected_9 = saved_frames
    image_V_map = {f"image_VQA_{i+1:02}": f"{video_stem}_V_{i+1}.jpg" for i in range(len(selected_9))}
    
    print(image_V_map)
    

    # image_VQA 폴더에 9장 복사 및 이름 변경
    for i, src_name in enumerate(selected_9):
        src_path = output_dir / src_name  # 원본 프레임에서 복사
        dst_name = f"{video_stem}_V_{i+1}.jpg"
        dst_path = image_V_dir / dst_name
        shutil.copy(src_path, dst_path)
        print(f"✅ VQA 이미지 복사: {src_name} → {dst_name}")

    return image_object_filenames, image_V_map


def create_vqa_metadata_and_save(video_name, image_object_filenames, image_V_map, output_dir, video_stem, output_dir_json):
    """
    VQA 유형 선택 및 메타데이터 생성 및 저장 함수
    
    Args:
        video_name (str): 비디오 파일명
        image_object_filenames (list): image_object 이미지 파일명 리스트
        image_V_map (dict): image_VQA 이미지 매핑
        output_dir (Path): JSON 파일을 저장할 디렉토리
        video_stem (str): 비디오 파일명 (확장자 제외)
        
    Returns:
        dict: 생성된 메타데이터
    """
    # VQA 유형 풀 정의
    vqa_types_pool = [
        "행동 순서 (Action Sequence)", "행동 예측 (Action Prediction)", "상반되는 행동 (Action Antonym)", 
        "세분화된 행동 (Fine-grained Action)", "예상치 못한 행동 (Unexpected Action)",
        "세분화된 자세 (Fine-grained Pose)", "객체 존재 유무 (Object Existence)", 
        "객체 상호작용 (Object Interaction)", "물리적 상호관계 (Physical relationship)", 
        "이동 방향 (Moving Direction)", "행동의 시간적 위치 (Action Localization)", 
        "장면 전환 (Scene Transition)", "객체 수 세기 (Object counting)", 
        "[인지추론] 인물 시점 공간 추론 (Egocentric Navigation)",
        "[인지추론] 상황 추론 (Episodic Reasoning)", "[인지추론] 가정법 추론 (Counterfactual Inference)"
    ]
    
    # VQA 유형 3개 랜덤 선택
    selected_vqa = random.sample(vqa_types_pool, 3)
    vqa_map = {f"VQA_type_{i+1:02}": v for i, v in enumerate(selected_vqa)}
    
    print("✅ VQA 유형 선택 완료:")
    for key, value in vqa_map.items():
        print(f"  {key}: {value}")

    t2_json_folder_path = output_dir_json

    #result = transform2(t2_json_folder_path)
    result = "test"

    # 메타데이터 구성
    output_data = {
        "video_file": video_name,
        "scene_summary" : result,
        "image_object": json.dumps(image_object_filenames, ensure_ascii=False),
        **image_V_map,
        **vqa_map
    }
    
    # JSON 파일 저장
    json_output_path = output_dir_json / f"{video_stem}_metadata.json"
    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False)
    
    print(f"✅ 메타데이터 저장 완료: {json_output_path}")
    return output_data

video_names = [
    "input.mp4"
]

for video_name in video_names:
# Culture, Drama, Entertainment, News
    category = "seonghoon_250821"
    video_path = fr"C:\guide\videos\{category}\{video_name}"
    output_dir = Path(fr"C:\guide\preset_data\{category}\{video_name}\extracted_frames")
    output_dir_json = Path(fr"C:\guide\preset_data\{category}\{video_name}")

    #추출한 이미지 저장 경로
    output_dir_vo = Path(fr"C:\guide\preset_data\{category}\{video_name}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 영상 길이 확인
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = frame_count / fps
    if duration_sec > 280:
        raise ValueError("❌ 영상 길이가 1분을 초과합니다.")

    # 함수 호출
    saved_frames = extract_frames_from_video(video_path, output_dir)
    video_stem = Path(video_path).stem

    image_object_filenames, image_V_map = process_images_and_create_folders(
        saved_frames, output_dir, output_dir_vo, video_stem
    )

    # VQA 메타데이터 생성 및 저장
    metadata = create_vqa_metadata_and_save(
        video_name, image_object_filenames, image_V_map, output_dir, video_stem, output_dir_json
    )



