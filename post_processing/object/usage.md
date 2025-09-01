"객체 데이터 후처리 코드"

- 작업제외이미지 필터링
  - `ChainData -> value -> extra -> label`에 "작업제외이미지"가 포함된 객체 삭제
  - `ChainData -> value -> object_name`에 "추가 작업 불가"가 포함된 객체 삭제

- 추가 작업 불가 객체 처리
  - `ChainData -> value -> object_name`에 "추가 작업 불가"가 포함된 객체 카운트
  - **5개 이상**: 해당 SourceValue 전체 삭제
  - **5개 미만**: "추가 :작업 불가" 객체만 제외하고 나머지 객체 유지
