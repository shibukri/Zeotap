


# validators.py
from typing import Any, Dict, List, Set
import re

class RuleValidator:
    """Utility class for validating rules and attributes"""
    
    # Supported operators
    COMPARISON_OPERATORS = {'>', '<', '>=', '<=', '=', '!='}
    LOGICAL_OPERATORS = {'AND', 'OR'}
    
    # Regular expression for basic rule syntax validation
    RULE_SYNTAX_PATTERN = r'^[().\w\s<>=!]+$'
    
    @classmethod
    def validate_rule_string(cls, rule_string: str) -> bool:
        """
        Validates the basic syntax of a rule string
        
        Args:
            rule_string: The rule string to validate
            
        Returns:
            bool: True if valid, raises ValidationError if invalid
            
        Raises:
            ValidationError: If the rule string is invalid
        """
        # Check for empty or non-string input
        if not rule_string or not isinstance(rule_string, str):
            raise ValidationError("Rule string must be a non-empty string")
            
        # Check basic syntax using regex
        if not re.match(cls.RULE_SYNTAX_PATTERN, rule_string):
            raise ValidationError("Rule string contains invalid characters")
            
        # Validate parentheses matching
        if not cls._validate_parentheses(rule_string):
            raise ValidationError("Mismatched parentheses in rule string")
            
        # Validate operators
        if not cls._validate_operators(rule_string):
            raise ValidationError("Invalid or misplaced operators in rule string")
            
        return True
    
    @staticmethod
    def _validate_parentheses(rule_string: str) -> bool:
        """Validates matching parentheses in the rule string"""
        stack = []
        for char in rule_string:
            if char == '(':
                stack.append(char)
            elif char == ')':
                if not stack:
                    return False
                stack.pop()
        return len(stack) == 0
    
    @classmethod
    def _validate_operators(cls, rule_string: str) -> bool:
        """Validates operators in the rule string"""
        # Split by spaces to check operators
        tokens = rule_string.split()
        for i, token in enumerate(tokens):
            if token in cls.COMPARISON_OPERATORS:
                # Check if comparison operator has operands on both sides
                if i == 0 or i == len(tokens) - 1:
                    return False
            elif token in cls.LOGICAL_OPERATORS:
                # Check if logical operator has expressions on both sides
                if i == 0 or i == len(tokens) - 1:
                    return False
        return True

    @staticmethod
    def validate_attributes(data: Dict[str, Any], required_attributes: Set[str]) -> bool:
        """
        Validates that all required attributes are present in the data
        
        Args:
            data: Dictionary containing attribute values
            required_attributes: Set of required attribute names
            
        Returns:
            bool: True if valid, raises ValidationError if invalid
            
        Raises:
            ValidationError: If required attributes are missing
        """
        missing_attrs = required_attributes - set(data.keys())
        if missing_attrs:
            raise ValidationError(f"Missing required attributes: {missing_attrs}")
        return True

