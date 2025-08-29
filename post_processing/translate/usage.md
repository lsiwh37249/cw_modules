# 모듈 정보 및 사용 방법

translate_batch_with_libre_translate(texts: List[str]) -> List[str]
- LibreTranslate 서버를 이용해 여러 한글 텍스트를 영어로 배치 번역  
- 번역 실패 시 원본 텍스트로 보완하고, 결과 개수를 원본과 맞춤

translate_object_names_batch(data: Dict[str, Any]) -> Dict[str, Any]
- JSON 데이터 내 `object_annotation`의 `object_name_kr`을 배치 번역  
- 번역 결과를 `object_name_en`에 저장하고 진행 로그 출력

main()
- 입력 JSON 파일을 읽어 `object_name_kr` 배치 번역 후 출력 JSON으로 저장  
- 처리 시간과 번역 성공/실패 로그를 콘솔에 표시



번역에 사용하는 API 정보
https://github.com/LibreTranslate/LibreTranslate?utm_source=chatgpt.com

사용 방법
```bash
$ docker pull libretranslate/libretranslate
$ docker run -it -p 5000:5000 libretranslate/libretranslate
```
