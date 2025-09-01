import logging
import os
from datetime import datetime

def setup_logging():
    """로깅 설정을 초기화합니다."""
    # 로그 디렉토리 생성
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # 현재 시간을 파일명에 포함
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f'{log_dir}/object_processing_{current_time}.log'
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()  # 콘솔에도 출력
        ]
    )

def get_logger(name='object_processing'):
    """로거 인스턴스를 반환합니다."""
    return logging.getLogger(name)
