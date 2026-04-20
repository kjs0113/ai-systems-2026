"""
Base Agent Abstract Class

모든 에이전트가 상속받는 추상 기본 클래스
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class BaseAgent(ABC):
    """에이전트 기본 클래스"""
    
    def __init__(self, name: str):
        """
        Args:
            name: 에이전트 이름
        """
        self.name = name
        self.status = "idle"
        self.errors: list = []
        self.execution_log: list = []
    
    @abstractmethod
    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        에이전트 실행 메서드 (구현 필수)
        
        Args:
            inputs: 입력 데이터 딕셔너리
            
        Returns:
            Dict[str, Any]: 실행 결과
        """
        pass
    
    def _log(self, message: str, level: str = "info"):
        """로그 기록"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": self.name,
            "level": level,
            "message": message
        }
        self.execution_log.append(log_entry)
    
    def _set_status(self, status: str):
        """상태 변경"""
        self.status = status
        self._log(f"Status changed to: {status}")
    
    def _add_error(self, error: str):
        """에러 추가"""
        self.errors.append({
            "timestamp": datetime.utcnow().isoformat(),
            "error": error
        })
        self._log(f"Error: {error}", level="error")
    
    def get_status(self) -> str:
        """현재 상태 반환"""
        return self.status
    
    def get_errors(self) -> list:
        """에러 목록 반환"""
        return self.errors
    
    def reset(self):
        """상태 초기화"""
        self.status = "idle"
        self.errors = []
        self.execution_log = []
        self._log("Agent reset")
