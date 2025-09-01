# 배치 번역 방식으로 한글 번역 (빠른 버전)
import json
import os
import time
import requests
from typing import Dict, Any, List

def translate_batch_with_google_free(texts: List[str]) -> List[str]:
    """여러 한글 텍스트를 한 번에 영어로 번역"""
    try:
        # 모든 텍스트를 하나의 문자열로 결합 (구분자: \n)
        combined_text = '\n'.join(texts)
        
        # 구글 번역 API 호출
        url = "https://translate.googleapis.com/translate_a/single"
        
        # 파라미터 설정
        params = {
            'client': 'gtx',
            'sl': 'ko',  # 한국어
            'tl': 'en',  # 영어
            'dt': 't',
            'q': combined_text
        }
        
        # API 호출
        response = requests.get(url, params=params)
        if response.status_code == 200:
            result = response.json()
            
            # 번역 결과를 개별 텍스트로 분리
            translated_texts = []
            current_text = ""
            
            for sentence in result[0]:
                if sentence[0]:  # 번역된 텍스트가 있는 경우
                    current_text += sentence[0]
                    if sentence[0].endswith('\n') or sentence[0].endswith('.'):
                        translated_texts.append(current_text.strip())
                        current_text = ""
            
            # 마지막 텍스트 처리
            if current_text:
                translated_texts.append(current_text.strip())
            
            # 원본 텍스트 개수와 번역 결과 개수가 다를 경우 처리
            if len(translated_texts) != len(texts):
                print(f"⚠️ 번역 결과 개수 불일치: 원본 {len(texts)}개, 번역 {len(translated_texts)}개")
                # 부족한 경우 원본으로 채움
                while len(translated_texts) < len(texts):
                    translated_texts.append(texts[len(translated_texts)])
            
            time.sleep(1)  # 요청 간격
            return translated_texts[:len(texts)]  # 원본 개수만큼 반환
        else:
            print(f"번역 실패: {response.status_code}")
            return texts
            
    except Exception as e:
        print(f"배치 번역 오류: {e}")
        return texts

def translate_batch_with_libre_translate(texts: List[str]) -> List[str]:
    """LibreTranslate로 배치 번역"""
    try:
        url = "https://libretranslate.de/translate"
        data = {
            "q": '\n'.join(texts),
            "source": "ko",
            "target": "en"
        }
        
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            translated_text = result["translatedText"]
            
            # 번역 결과를 개별 텍스트로 분리
            translated_texts = [text.strip() for text in translated_text.split('\n')]
            
            # 원본 개수와 맞추기
            if len(translated_texts) != len(texts):
                while len(translated_texts) < len(texts):
                    translated_texts.append(texts[len(translated_texts)])
            
            time.sleep(1)
            return translated_texts[:len(texts)]
        else:
            print(f"번역 실패: {response.status_code}")
            return texts
            
    except Exception as e:
        print(f"배치 번역 오류: {e}")
        return texts

def translate_object_names_batch(data: Dict[str, Any]) -> Dict[str, Any]:
    """object_name_kr의 한글 값들을 배치로 번역하여 object_name_en에 저장"""
    if 'object_annotation' in data:
        # 번역할 한글 텍스트들 수집
        korean_texts = []
        text_to_obj_map = []  # 텍스트와 객체의 매핑
        
        for obj in data['object_annotation']:
            if 'object_name_kr' in obj and obj['object_name_kr']:
                korean_texts.append(obj['object_name_kr'])
                text_to_obj_map.append(obj)
        
        if not korean_texts:
            print("번역할 한글 텍스트가 없습니다.")
            return data
        
        print(f"📝 총 {len(korean_texts)}개 텍스트 배치 번역 시작...")
        print(f"번역할 텍스트: {', '.join(korean_texts)}")
        
        # 배치 번역 시도
        english_texts = translate_batch_with_google_free(korean_texts)
        
        # 첫 번째 방법 실패 시 두 번째 방법 시도
        if english_texts == korean_texts:
            print("Google 번역 실패, LibreTranslate 시도...")
            english_texts = translate_batch_with_libre_translate(korean_texts)
        
        # 번역 결과를 각 객체에 적용
        for i, obj in enumerate(text_to_obj_map):
            if i < len(english_texts):
                korean_name = obj['object_name_kr']
                english_name = english_texts[i]
                obj['object_name_en'] = english_name
                
                if english_name == korean_name:
                    print(f"⚠️ 번역 실패: {korean_name}")
                else:
                    print(f"✅ 번역: {korean_name} -> {english_name}")
        
        print(f"🎉 배치 번역 완료! {len(korean_texts)}개 텍스트 처리됨")
    
    return data

def main():
    # 입력 JSON 파일 경로
    input_file = '../data/result/result.json'
    
    # 출력 JSON 파일 경로
    output_file = '../data/result/result_translated_batch.json'
    
    # 입력 파일 읽기
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"입력 파일 로드 완료: {input_file}")
    except FileNotFoundError:
        print(f"입력 파일을 찾을 수 없습니다: {input_file}")
        return
    except json.JSONDecodeError:
        print("JSON 파일 형식이 올바르지 않습니다.")
        return
    
    # 배치 번역 처리
    print("한글 -> 영어 배치 번역 시작...")
    start_time = time.time()
    translated_data = translate_object_names_batch(data)
    end_time = time.time()
    
    print(f"⏱️ 번역 소요 시간: {end_time - start_time:.2f}초")
    
    # 출력 디렉토리 생성
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 번역된 파일 저장
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(translated_data, f, indent=2, ensure_ascii=False)
        print(f"번역 완료! 출력 파일: {output_file}")
    except Exception as e:
        print(f"파일 저장 오류: {e}")

if __name__ == "__main__":
    main()
