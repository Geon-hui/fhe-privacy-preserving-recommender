import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logger(name, log_file=None, level=logging.INFO):
    """
    통합 로거 설정
    - 콘솔과 파일에 동시 출력
    - 에러는 별도 파일에 기록
    """
    # 로그 디렉토리 생성
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 기존 핸들러 제거 (중복 방지)
    logger.handlers.clear()
    
    # 포맷 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 (전체 로그)
    if log_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f'{name}_{timestamp}.log'
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 에러 전용 파일 핸들러
    error_file = log_dir / f'{name}_errors.log'
    error_handler = logging.FileHandler(error_file, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    return logger

def log_exception(logger, exception, context=""):
    """
    예외를 상세히 로깅
    """
    import traceback
    
    error_msg = f"Exception occurred"
    if context:
        error_msg += f" in {context}"
    
    logger.error(error_msg, exc_info=True)
    logger.error(f"Exception type: {type(exception).__name__}")
    logger.error(f"Exception message: {str(exception)}")
    logger.error(f"Traceback:\n{''.join(traceback.format_tb(exception.__traceback__))}")
