"""
유틸리티 데코레이터 모듈
"""
import time
import functools
from typing import Callable, Any
import ccxt
import requests
from utils.logger import logger

def retry_on_network_error(max_retries: int = 3, delay: float = 1.0):
    """네트워크 에러 발생 시 재시도하는 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (requests.exceptions.RequestException, 
                        ccxt.NetworkError, 
                        ccxt.ExchangeNotAvailable,
                        ccxt.RequestTimeout) as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"네트워크 에러 발생 (시도 {attempt + 1}/{max_retries}): {e}")
                        time.sleep(delay * (2 ** attempt))  # 지수 백오프
                        continue
                    else:
                        logger.error(f"네트워크 에러 - 최대 재시도 횟수 초과: {e}")
                        raise
                except Exception as e:
                    logger.error(f"예상치 못한 에러: {e}")
                    raise
            return None
        return wrapper
    return decorator

def log_execution_time(func: Callable) -> Callable:
    """함수 실행 시간을 로그하는 데코레이터"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        
        logger.debug(f"{func.__name__} 실행 시간: {execution_time:.2f}초")
        return result
    return wrapper

def handle_exceptions(default_return: Any = None):
    """예외 처리 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"{func.__name__} 실행 중 오류: {e}")
                return default_return
        return wrapper
    return decorator

def rate_limit(calls_per_second: float = 1.0):
    """API 호출 속도 제한 데코레이터"""
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator

def cache_result(cache_time: int = 300):
    """결과 캐싱 데코레이터 (초 단위)"""
    cache = {}
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 캐시 키 생성
            cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
            current_time = time.time()
            
            # 캐시 확인
            if cache_key in cache:
                cached_time, cached_result = cache[cache_key]
                if current_time - cached_time < cache_time:
                    logger.debug(f"{func.__name__} 캐시 결과 반환")
                    return cached_result
            
            # 함수 실행 및 결과 캐싱
            result = func(*args, **kwargs)
            cache[cache_key] = (current_time, result)
            
            # 오래된 캐시 정리
            expired_keys = [key for key, (cached_time, _) in cache.items() 
                           if current_time - cached_time >= cache_time]
            for key in expired_keys:
                del cache[key]
            
            return result
        return wrapper
    return decorator

def validate_parameters(**validations):
    """매개변수 유효성 검사 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 함수 시그니처 검사
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # 유효성 검사
            for param_name, validator in validations.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not validator(value):
                        raise ValueError(f"잘못된 매개변수 값: {param_name}={value}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def monitor_performance(func: Callable) -> Callable:
    """성능 모니터링 데코레이터"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        import psutil
        import os
        
        # 시작 시점 메트릭
        start_time = time.time()
        process = psutil.Process(os.getpid())
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 함수 실행
        result = func(*args, **kwargs)
        
        # 종료 시점 메트릭
        end_time = time.time()
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 성능 로그
        execution_time = end_time - start_time
        memory_usage = end_memory - start_memory
        
        logger.debug(f"{func.__name__} 성능 - 시간: {execution_time:.2f}초, 메모리: {memory_usage:+.2f}MB")
        
        return result
    return wrapper