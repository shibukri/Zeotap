# constants.py
class RuleConstants:
    """Constants used throughout the Rule Engine"""
    
    # Node types
    NODE_TYPE_OPERATOR = "operator"
    NODE_TYPE_OPERAND = "operand"
    
    # Operator types
    OPERATOR_AND = "AND"
    OPERATOR_OR = "OR"
    OPERATOR_GT = ">"
    OPERATOR_LT = "<"
    OPERATOR_GTE = ">="
    OPERATOR_LTE = "<="
    OPERATOR_EQ = "="
    OPERATOR_NEQ = "!="
    
    # Supported attributes
    SUPPORTED_ATTRIBUTES = {
        'age': int,
        'department': str,
        'salary': (int, float),
        'experience': (int, float),
        'spend': (int, float)
    }
    
    # Maximum limits
    MAX_RULE_LENGTH = 1000
    MAX_NESTED_DEPTH = 10
    MAX_COMBINED_RULES = 50

