#!/usr/bin/env python3
"""
Video LLM Analysis Script
영상 이미지 분석을 위한 통합 스크립트
"""

import os
import base64
import google.generativeai as genai
import json
import re
import glob

def setup_gemini_api():
    """Gemini API 설정"""
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
    
    genai.configure(api_key=GEMINI_API_KEY)
    print("✅ Gemini API 설정 완료!")
    return True

def encode_image(file_path):
    """이미지 파일을 Base64로 인코딩"""
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def get_images_from_folder(folder_path):
    """
    지정된 폴더에서 _V_가 포함된 이미지 파일들만 찾아 리스트로 반환
    
    Args:
        folder_path (str): 이미지가 있는 폴더 경로
        
    Returns:
        list: _V_가 포함된 이미지 파일 경로들의 리스트
    """
    # 경로가 존재하는지 확인
    if not os.path.exists(folder_path):
        raise ValueError(f"경로가 존재하지 않습니다: {folder_path}")
    
    # 이미지 파일 패턴들
    image_patterns = ['*.jpg', '*.jpeg', '*.png']
    image_files = []
    
    # 각 패턴으로 파일 찾기
    for pattern in image_patterns:
        image_files.extend(glob.glob(os.path.join(folder_path, pattern)))
    
    # _V_가 포함된 파일들만 필터링
    v_images = []
    for file_path in image_files:
        file_name = os.path.basename(file_path)
        if '_V_' in file_name:
            v_images.append(file_path)
    
    # 중복 제거 (파일명 기준, 대소문자 무시)
    unique_files = []
    seen_names = set()
    
    for file_path in v_images:
        file_name = os.path.basename(file_path).lower()
        if file_name not in seen_names:
            seen_names.add(file_name)
            unique_files.append(file_path)
    
    # 파일명 기준으로 정렬
    unique_files.sort()
    
    # 디버깅 정보 출력
    print(f"전체 이미지 파일 수: {len(image_files)}")
    print(f"_V_ 포함 이미지 파일 수: {len(unique_files)}")
    print(f"첫 번째 _V_ 이미지: {unique_files[0] if unique_files else '없음'}")
    
    # _V_ 포함 파일 목록 출력
    print("\n=== _V_ 포함 이미지 파일 목록 ===")
    for i, file_path in enumerate(unique_files):
        file_name = os.path.basename(file_path)
        print(f"{i+1:2d}. {file_name}")
    
    return unique_files

def create_analysis_prompt(image_count):
    """이미지 분석을 위한 프롬프트 생성"""
    prompt = f"""
    [Goal]
    {{미디어 장면 이미지에 대해 배경, 행동, 분위기, 장소 등 구체적으로 묘사하되 요약문 형태로 작성}}

    [Role]
    {{너는 영상 내 장면 정보를 소개하는 크리에이터이자 검색 기반으로 영상을 편집해야하는 편집자이다. 경어를 사용하지 않고 -이다. 또는 -중이다.와 같은 현재형 형태로만 작성한다.}}

    [Context]
    {{프로젝트는 방송 미디어로 보도, 시사교양, 드라마, 예능 등으로 구성되어 있으며 민감정보인 이목구비를 포함한 얼굴, 번호판 등 비식별되므로 표현해서는 안된다.}}

    [Task]
    1. 이미지 번호 순서대로 식별.
    2. 각 이미지마다 인물의 행동, 주변 배경, 장소 분위기 등 다양한 형용사적 표현을 포함해 묘사.
    3. 이미지를 순서대로 묘사하되, 최종 출력은 모든 문장을 하나의 단락으로 병합해 제시.
    4. 입력된 이미지는 총 {image_count}장이며, 각 이미지당 정확히 한 문장씩 작성해 총 {image_count}문장을 출력한다. 누락·합병 금지.

    [Constraints]
    - 이미지 세트 전체 {image_count}문장 (입력 이미지 수와 동일).
    - 한국어로만.
    - 경어 금지.
    - 종결어미 규칙
    1) 동작·행위 → "-고 있다" 또는 "-중이다" (한 문장 안에서는 하나만 사용).
    2) 정적 속성·형태 → "-이다".
    3) 위치·존재 → "-에 있다".
    4) 추측·번역체 금지: "-하는 상태이다", "-듯하다" 등 사용 금지.
    5) 사물 표현 이중 피동·사동 금지 : "-되어지고 있다." 등 사용 금지.
    - 이목구비로 나타낼 수 있는 행동 묘사 금지.
    - 얼굴·번호판·표정 등 비식별·추론·유추 표현 금지.
    - 출력 문장은 각 문장 끝에 반드시 마침표('.').
    - '있고 있으며·하고 있으며' 등 이어말하기 접속 구조 금지 (문장 단위로 끊기).
    - 출력에 파일명·번호·범위 등 메타 정보 표기 금지.

    [Output]
    <한 문장당 하나의 행동·배경·분위기 기술 후 마침표로 구분>
    """
    return prompt.strip()

def create_get_object_prompt(image_count):
    """
    이미지 분석을 위한 프롬프트 생성
    """
    prompt = f"""
    당신은 이미지 분석 전문가입니다. 제공된 이미지에서 객체 추출 작업을 수행해주세요.

    **분석 절차:**
    1단계: 이미지 전체를 스캔하며 식별 가능한 모든 객체 파악
    2단계: 요약된 이미지 정보를 기반으로 객체 추출출
    3단계: 각 객체를 적절한 일반명사로 분류

    **출력 형식:**
    1번 이미지: [객체1, 객체2, 객체3, ...]
    2번 이미지: [객체1, 객체2, 객체3, ...]
    3번 이미지: [객체1, 객체2, 객체3, ...]

    ...

    **명명 규칙:**
    - 특정 브랜드명이나 모델명 사용 금지 (예: "아이폰" → "스마트폰")
    - 일반적인 카테고리명 사용 (예: "노트북", "커피잔", "책")
    - 한국어 명사로 표현
    - 같은 종류의 여러 객체가 있으면 개수 포함 (예: "사과 3개")

    **포함 기준:**
    - 명확하게 식별되는 사물, 음식, 물건만 포함
    - 배경, 벽, 바닥 등은 제외
    - 확신도가 높은 객체만 포함
    - 부분적으로 보이더라도 명확히 식별되면 포함

    **크기 기준:**
    - 이미지에서 차지하는 비율이 1% 이상인 객체만 포함
    - 너무 작아서 정확히 식별하기 어려운 객체는 제외

    **판단 기준:**
    - 두 개 이상의 해석이 가능한 경우, 더 일반적인 명칭 사용
    - 용도가 불분명한 객체는 외관 기반으로 명명 (예: "원형 그릇", "긴 막대")
    - 확신도가 낮으면 상위 카테고리로 분류 (예: "전자기기", "용기")

    **제외 대상:**
    - 텍스트나 글자 (간판, 라벨 등)
    - 그림자, 반사, 빛
    - 로고, 패턴, 장식
    - 건축 구조물 (문, 창문, 계단 등)
    """
    return prompt.strip()

def combined_prompt(image_count):
    """이미지 분석을 위한 프롬프트 생성"""
    prompt = f"""
    총 2개의 프롬프트를 합친 프롬프트입니다.
    1. 이미지 분석을 위한 프롬프트
    2. 객체 추출을 위한 프롬프트

    1. 이미지 분석을 위한 프롬프트
    [Goal]
    {{미디어 장면 이미지에 대해 배경, 행동, 분위기, 장소 등 구체적으로 묘사하되 요약문 형태로 작성}}

    [Role]
    {{너는 영상 내 장면 정보를 소개하는 크리에이터이자 검색 기반으로 영상을 편집해야하는 편집자이다. 경어를 사용하지 않고 -이다. 또는 -중이다.와 같은 현재형 형태로만 작성한다.}}

    [Context]
    {{프로젝트는 방송 미디어로 보도, 시사교양, 드라마, 예능 등으로 구성되어 있으며 민감정보인 이목구비를 포함한 얼굴, 번호판 등 비식별되므로 표현해서는 안된다.}}

    [Task]
    1. 이미지 번호 순서대로 식별.
    2. 각 이미지마다 인물의 행동, 주변 배경, 장소 분위기 등 다양한 형용사적 표현을 포함해 묘사.
    3. 이미지를 순서대로 묘사하되, 최종 출력은 모든 문장을 하나의 단락으로 병합해 제시.
    4. 입력된 이미지는 총 {image_count}장이며, 각 이미지당 정확히 한 문장씩 작성해 총 {image_count}문장을 출력한다. 누락·합병 금지.

    [Constraints]
    - 이미지 세트 전체 {image_count}문장 (입력 이미지 수와 동일).
    - 한국어로만.
    - 경어 금지.
    - 종결어미 규칙
    1) 동작·행위 → "-고 있다" 또는 "-중이다" (한 문장 안에서는 하나만 사용).
    2) 정적 속성·형태 → "-이다".
    3) 위치·존재 → "-에 있다".
    4) 추측·번역체 금지: "-하는 상태이다", "-듯하다" 등 사용 금지.
    5) 사물 표현 이중 피동·사동 금지 : "-되어지고 있다." 등 사용 금지.
    - 이목구비로 나타낼 수 있는 행동 묘사 금지.
    - 얼굴·번호판·표정 등 비식별·추론·유추 표현 금지.
    - 출력 문장은 각 문장 끝에 반드시 마침표('.').
    - '있고 있으며·하고 있으며' 등 이어말하기 접속 구조 금지 (문장 단위로 끊기).
    - 출력에 파일명·번호·범위 등 메타 정보 표기 금지.

    [Output]
    <한 문장당 하나의 행동·배경·분위기 기술 후 마침표로 구분>

    2. 객체 추출을 위한 프롬프트
    당신은 이미지 분석 전문가입니다. 제공된 이미지에서 객체 추출 작업을 수행해주세요.

    요약된 이미지 정보 : 군복을 입은 남자가 펜을 든 채 책상에 앉아 진지한 표정으로 정면을 응시하고 있다. 태권도복을 입은 건장한 체격의 남자가 한쪽 다리를 들고 발차기 동작을 하고 있으며, 두 손은 방어 자세를 취하고 있다. 태권도복을 입은 동일한 남자가 불편한 표정으로 두 손을 얼굴 가까이 모은 채 동작을 마무리하고 있다. 어두운 군복을 입은 남자가 서류를 검토하며 마이크에 대고 이야기하고 있으며, 옆에는 군복을 입은 다른 두 남자가 앉아 있다. 태권도복을 입은 건장한 남자가 보호 붕대를 감은 손을 내려다보며 실망한 표정을 짓고 있다. 검은색 브이넥 칼라 태권도복을 입은 또 다른 사람이 고통스러운 표정으로 아래를 보며 주먹으로 바닥을 치고 있다. 검은색 브이넥 태권도복을 입은 사람이 찡그린 표정으로 팔을 힘껏 내리치고 있다. 검은색 브이넥 태권도복을 입은 남자가 허리를 굽히고 팔을 내린 채 아래를 내려다보고 있다. 건장한 남자가 다른 두 사람과 함께 앉아 있는데, 한 사람은 웃고 있고 그는 걱정스러운 표정으로 입을 가리고 있다.

    **분석 절차:**
    1단계: 이미지 전체를 스캔하며 식별 가능한 모든 객체 파악
    2단계: 요약된 이미지 정보를 기반으로 객체 추출출
    3단계: 각 객체를 적절한 일반명사로 분류

    **출력 형식:**
    다음과 같이 단순 리스트로 작성해주세요:

    [객체명1, 객체명2, 객체명3]

    ...

    **명명 규칙:**
    - 특정 브랜드명이나 모델명 사용 금지 (예: "아이폰" → "스마트폰")
    - 일반적인 카테고리명 사용 (예: "노트북", "커피잔", "책")
    - 한국어 명사로 표현
    - 같은 종류의 여러 객체가 있으면 개수 포함 (예: "사과 3개")

    **포함 기준:**
    - 명확하게 식별되는 사물, 음식, 물건만 포함
    - 배경, 벽, 바닥 등은 제외
    - 확신도가 높은 객체만 포함
    - 부분적으로 보이더라도 명확히 식별되면 포함

    **크기 기준:**
    - 이미지에서 차지하는 비율이 1% 이상인 객체만 포함
    - 너무 작아서 정확히 식별하기 어려운 객체는 제외

    **판단 기준:**
    - 두 개 이상의 해석이 가능한 경우, 더 일반적인 명칭 사용
    - 용도가 불분명한 객체는 외관 기반으로 명명 (예: "원형 그릇", "긴 막대")
    - 확신도가 낮으면 상위 카테고리로 분류 (예: "전자기기", "용기")

    **제외 대상:**
    - 텍스트나 글자 (간판, 라벨 등)
    - 그림자, 반사, 빛
    - 로고, 패턴, 장식
    - 건축 구조물 (문, 창문, 계단 등)
    """
    return prompt.strip()

def analyze_images_with_gemini(encoded_images, image_count):
    """
    Gemini API를 사용하여 이미지들을 분석
    
    Args:
        encoded_images (list): Base64로 인코딩된 이미지 데이터 리스트
        image_count (int): 이미지 개수
        
    Returns:
        str: Gemini API 응답 텍스트
    """
    # 모델 생성
    model = genai.GenerativeModel("gemini-2.5-pro")
    print(f"사용할 모델: {model.model_name}")
    
    # 프롬프트 생성
    prompt = create_analysis_prompt(image_count)
    print(f"프롬프트에 전달된 이미지 개수: {image_count}")
    
    # 입력 데이터 구성
    parts = [{"text": prompt}]
    parts.extend([
        {"inline_data": {"mime_type": "image/jpeg", "data": img}} 
        for img in encoded_images
    ])
    
    # API 호출
    print("API 호출 중...")
    response = model.generate_content(parts)
    
    print("=== Gemini 응답 ===")
    print("원본 응답:")
    print(response.text)
    print(response)
    
    return response.text

def transform2(folder_path):

    # 1단계: Gemini API 설정
    setup_gemini_api()
        
    # 2단계: 이미지 파일 수집
    image_paths = get_images_from_folder(folder_path)
    print(f"✅ {len(image_paths)}개 이미지 파일 발견")
        
    # 3단계: 이미지 Base64 인코딩
    encoded_images = [encode_image(path) for path in image_paths]
    print(f"✅ {len(encoded_images)}개 이미지 인코딩 완료")
        
    # 4단계: Gemini API로 이미지 분석
    gemini_response = analyze_images_with_gemini(encoded_images, len(image_paths))
    print("✅ Gemini API 분석 완료")

    return gemini_response
        
if __name__ == "__main__":
    folder_path = r"C:\guide\preset_data\20\MBC_sample_HelpMeHolmes_20250612_2.mp4"
    # 1단계: Gemini API 설정
    result = transform2(folder_path)
    print(result)
    if result:
        print("✅ 프로그램이 성공적으로 완료되었습니다.")
    else:
        print("❌ 프로그램 실행에 실패했습니다.")
