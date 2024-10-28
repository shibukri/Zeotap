# exceptions.py
class RuleEngineException(Exception):
    """Base exception class for Rule Engine"""
    pass

class RuleParsingError(RuleEngineException):
    """Raised when there's an error parsing a rule string"""
    pass

class RuleEvaluationError(RuleEngineException):
    """Raised when there's an error evaluating a rule"""
    pass

class RuleCombiningError(RuleEngineException):
    """Raised when there's an error combining rules"""
    pass

class ValidationError(RuleEngineException):
    """Raised when there's a validation error"""
    pass

