# helpers.py
from typing import Any, Dict, Optional
from .constants import RuleConstants
from .exceptions import ValidationError

class RuleHelper:
    """Helper utilities for rule processing"""
    
    @staticmethod
    def validate_attribute_type(attr_name: str, value: Any) -> bool:
        """
        Validates that an attribute value matches its expected type
        
        Args:
            attr_name: Name of the attribute
            value: Value to validate
            
        Returns:
            bool: True if valid, raises ValidationError if invalid
        """
        expected_type = RuleConstants.SUPPORTED_ATTRIBUTES.get(attr_name)
        if not expected_type:
            raise ValidationError(f"Unsupported attribute: {attr_name}")
            
        if isinstance(expected_type, tuple):
            if not isinstance(value, expected_type):
                raise ValidationError(
                    f"Invalid type for {attr_name}. Expected {expected_type}, got {type(value)}"
                )
        else:
            if not isinstance(value, expected_type):
                raise ValidationError(
                    f"Invalid type for {attr_name}. Expected {expected_type}, got {type(value)}"
                )
        return True
    
    @staticmethod
    def format_rule_string(rule_string: str) -> str:
        """
        Formats a rule string for consistent processing
        
        Args:
            rule_string: Rule string to format
            
        Returns:
            str: Formatted rule string
        """
        # Remove extra whitespace
        formatted = ' '.join(rule_string.split())
        # Ensure spaces around operators
        for op in ['(', ')', '>', '<', '=', '!=', '>=', '<=']:
            formatted = formatted.replace(op, f' {op} ')
        return ' '.join(formatted.split())
    
    @staticmethod
    def get_nested_depth(ast_dict: Dict) -> int:
        """
        Calculates the nested depth of an AST
        
        Args:
            ast_dict: Dictionary representation of AST
            
        Returns:
            int: Maximum nested depth
        """
        if not ast_dict:
            return 0
            
        left_depth = 0
        right_depth = 0
        
        if 'left' in ast_dict:
            left_depth = RuleHelper.get_nested_depth(ast_dict['left'])
        if 'right' in ast_dict:
            right_depth = RuleHelper.get_nested_depth(ast_dict['right'])
            
        return max(left_depth, right_depth) + 1
