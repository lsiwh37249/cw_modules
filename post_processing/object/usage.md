# 객체 데이터 처리 흐름 상세 분석

## 1. 전체 처리 흐름 개요

### 1.1 메인 처리 함수 (`object_post_processing.py`)
```python
def post_processing(data: Dict[str, Any]):
    # 1. 템플릿 초기화
    base_format_data = json.load(open('../../data/format/객체 데이터 포맷.txt', 'r', encoding='utf-8'))
    null_template = initialize_template(base_format_data)

    # 2. 기본 데이터 추가
    first_template = add_base(null_template, data)

    # 3. 영상 데이터 추가
    second_template = add_video(first_template, data)

    # 4. 클립 데이터 추가
    third_template = add_clip(second_template, data)

    # 5. 객체 어노테이션 추가
    final_template = add_object_annotation(third_template, data)

    return final_template
```

## 2. 세부 처리 단계

### 2.1 템플릿 초기화 (`initialize_template`)
- **목적**: 기본 포맷 템플릿을 null 값으로 초기화
- **처리**: 딕셔너리와 리스트 구조를 유지하면서 모든 값을 None으로 설정

### 2.2 기본 데이터 추가 (`add_base`)
- **추가 데이터**:
  - `dataID`: 원본 데이터의 ID
  - `dataset_name`: "example_dataset"
  - `version`: "v1.0"
  - `year`: "2025"
  - `category`: [None]
  - `subject`: [None]

### 2.3 영상 데이터 추가 (`add_video`)
- **처리**: `importData_video_file`에서 파일명 추출
- **정제**: 확장자 제거 후 마지막 숫자 부분 제거
- **결과**: video 배열에 id, width, height, file_name 포함

### 2.4 클립 데이터 추가 (`add_clip`)
- **처리**: 비디오 파일 정보를 클립 형태로 변환
- **결과**: clip 객체에 id, file_name, length, format 등 포함

### 2.5 객체 어노테이션 처리 (`add_object_annotation`)

#### 2.5.1 데이터 구조 확인
```python
if "object" in data and "data" in data["object"]:
    object_data = data["object"]["data"]
```

#### 2.5.2 SourceValue별 처리
각 SourceValue(이미지)에 대해:
1. **ChainData 필터링** (`filter_chain_data`)
2. **추가 작업 불가 객체 카운트**
3. **조건부 처리 결정**

### 2.6 ChainData 필터링 (`filter_chain_data`)

#### 2.6.1 제외 조건 체크
1. **작업제외이미지**:
   - `extra.label`에 "작업제외이미지" 포함

2. **추가 작업 불가 객체**:
   - `object_name`에 "추가 작업 불가" 포함

#### 2.6.2 반환값
- `valid_chain_items`: 유효한 체인 아이템들
- `additional_work_impossible_count`: 추가 작업 불가 객체 수

### 2.7 조건부 처리 로직

#### Case 1: 추가 작업 불가 객체가 5개 이상
```python
if additional_work_impossible_count >= 5:
    logger.warning(f"추가 작업 불가 객체가 {additional_work_impossible_count}개로 5개 이상이므로 이 SourceValue 전체 삭제")
    continue  # 해당 SourceValue 전체 건너뛰기
```

#### Case 2: 추가 작업 불가 객체가 5개 미만
```python
else:
    logger.info(f"추가 작업 불가 객체가 {additional_work_impossible_count}개로 5개 미만이므로 처리 진행")
    new_annotations, frame_counter = process_valid_chain_items(
        valid_chain_items, source_image, frame_counter
    )
    object_annotations.extend(new_annotations)
```

### 2.8 유효한 체인 아이템 처리 (`process_valid_chain_items`)

#### 2.8.1 핵심 데이터 추출
```python
object_annotation = {
    "image_id": source_image,           # 실제 이미지 파일명
    "object_id": chain_item["objectID"], # 객체 ID
    "image_frame": "",                  # 프레임 번호 (현재 미사용)
    "object_name_kr": object_name,      # 한글 객체명
    "object_name_en": "",              # 영어 객체명 (현재 미사용)
    "bbox": bbox                        # 바운딩 박스 좌표
}
```

#### 2.8.2 바운딩 박스 생성
```python
bbox = [
    coords["tl"]["x"],              # top-left x
    coords["tl"]["y"],              # top-left y
    value["object"]["width"],       # 이미 계산된 width
    value["object"]["height"]       # 이미 계산된 height
]
```

## 3. 데이터 흐름 요약

```
JSON 파일 → 한 줄씩 읽기 → post_processing()
    ↓
템플릿 초기화 → 기본/영상/클립 데이터 추가
    ↓
add_object_annotation()
    ↓
SourceValue별로 ChainData 필터링
    ↓
filter_chain_data() → 작업제외이미지/추가작업불가 객체 분류
    ↓
조건부 처리:
- 5개 이상: SourceValue 전체 삭제
- 5개 미만: process_valid_chain_items()로 핵심 데이터 추출
    ↓
최종 object_annotations 배열 생성
```

## 4. 주요 제외 조건

1. **작업제외이미지**: `extra.label` 또는 `object_name`에 "작업제외이미지" 포함
2. **추가 작업 불가**: `object_name`에 "추가 작업 불가" 포함
3. **SourceValue 전체 삭제**: 해당 SourceValue의 추가 작업 불가 객체가 5개 이상인 경우

## 5. 로깅 및 모니터링

- 각 단계별 상세 로깅
- 처리된 객체 수, 제외된 객체 수, 생성된 어노테이션 수 추적
- 오류 발생 시 상세한 에러 메시지와 스택 트레이스 기록
  
