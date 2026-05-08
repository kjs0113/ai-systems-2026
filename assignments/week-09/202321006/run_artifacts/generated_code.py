class Calculator:
    """두 숫자를 더하는 간단한 계산기 클래스"""
    
    def add(self, a: float, b: float) -> float:
        """
        두 숫자를 더합니다.
        결과가 100을 초과하면 ValueError를 발생시킵니다.
        """
        result = a + b
        if result > 100:
            raise ValueError("결과값이 100을 초과할 수 없습니다.")
        return result
