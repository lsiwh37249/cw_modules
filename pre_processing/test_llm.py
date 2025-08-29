import os
import base64
import google.generativeai as genai
import json
import re
import glob
from video_llm_RnD import get_images_from_folder, encode_image, create_analysis_prompt, combined_prompt, create_get_object_prompt, analyze_images_with_gemini


folder_path = r"C:\guide\preset_data\4_250812\MBC_sample_I_Live_Alone_20250530_6.mp4"

image_paths = get_images_from_folder(folder_path)

encoded_images = [encode_image(path) for path in image_paths]

gemini_response = analyze_images_with_gemini(encoded_images, len(image_paths))

model = genai.GenerativeModel("gemini-1.5-flash")
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

gemini_response = response.text

if gemini_response:
    print("✅ 프로그램이 성공적으로 완료되었습니다.")
else:
    print("❌ 프로그램 실행에 실패했습니다.")