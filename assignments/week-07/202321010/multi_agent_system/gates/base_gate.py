"""
Base Gate Class

모든 검증 게이트가 상속받는 기본 클래스
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from datetime import datetime


class ValidationResult:
    """검증 결과 클래스"""
    
    def __init__(self, passed: bool, gate_name: str):
        self.passed = passed
        self.gate_name = gate_name
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.timestamp = datetime.utcnow().isoformat()
    
    def add_error(self, error: str):
        """에러 추가"""
        self.errors.append(error)
        self.passed = False
    
    def add_warning(self, warning: str):
        """경고 추가"""
        self.warnings.append(warning)
    
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            "gate": self.gate_name,
            "passed": self.passed,
            "errors": self.errors,
            "warnings": self.warnings,
            "timestamp": self.timestamp
        }


class BaseGate(ABC):
    """검증 게이트 기본 클래스"""
    
    def __init__(self, name: str):
        self.name = name
        self.checklist: List[str] = []
    
    @abstractmethod
    def validate(self, artifact: Any) -> ValidationResult:
        """
        검증 수행 (구현 필수)
        
        Args:
            artifact: 검증할 아티팩트
            
        Returns:
            ValidationResult: 검증 결과
        """
        pass
    
    def get_checklist(self) -> List[str]:
        """체크리스트 반환"""
        return self.checklist
