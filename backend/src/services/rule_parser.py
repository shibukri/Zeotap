from typing import List, Tuple
import re
from ..models.ast_node import ASTNode, NodeType, Operator
from ..utils.exceptions import RuleParsingError

class RuleParser:
    def __init__(self):
        self.operators = {
            'AND': 1,
            'OR': 1,
            '>': 2,
            '<': 2,
            '=': 2,
            '>=': 2,
            '<=': 2
        }
        
    def tokenize(self, rule_string: str) -> List[str]:
        # Replace parentheses with spaces around them
        rule_string = re.sub(r'([()])', r' \1 ', rule_string)
        
        # Split the string into tokens
        tokens = rule_string.split()
        
        # Process tokens to handle string literals
        processed_tokens = []
        current_string = []
        in_string = False
        
        for token in tokens:
            if token.startswith("'") and token.endswith("'"):
                processed_tokens.append(token)
            elif token.startswith("'"):
                in_string = True
                current_string.append(token)
            elif token.endswith("'"):
                in_string = False
                current_string.append(token)
                processed_tokens.append(' '.join(current_string))
                current_string = []
            elif in_string:
                current_string.append(token)
            else:
                processed_tokens.append(token)
        
        return processed_tokens

    def parse(self, rule_string: str) -> ASTNode:
        tokens = self.tokenize(rule_string)
        return self._parse_expression(tokens)

    def _parse_expression(self, tokens: List[str]) -> ASTNode:
        if not tokens:
            raise RuleParsingError("Empty expression")

        # Handle parentheses
        if tokens[0] == '(':
            # Find matching closing parenthesis
            count = 1
            i = 1
            while i < len(tokens) and count > 0:
                if tokens[i] == '(':
                    count += 1
                elif tokens[i] == ')':
                    count -= 1
                i += 1
            
            if count != 0:
                raise RuleParsingError("Mismatched parentheses")
                
            return self._parse_expression(tokens[1:i-1])

        # Find the operator with lowest precedence
        min_precedence = float('inf')
        operator_index = -1
        
        for i, token in enumerate(tokens):
            if token in self.operators:
                if self.operators[token] < min_precedence:
                    min_precedence = self.operators[token]
                    operator_index = i

        if operator_index == -1:
            # This must be a comparison
            if len(tokens) != 3:
                raise RuleParsingError(f"Invalid comparison: {' '.join(tokens)}")
                
            field, op, value = tokens
            
            # Clean up string literals
            if value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            # Convert numeric values
            elif value.isdigit():
                value = int(value)
            elif value.replace('.', '').isdigit():
                value = float(value)

            return ASTNode(
                type=NodeType.COMPARISON,
                operator=Operator(op),
                field=field,
                value=value
            )

        # Split on operator and recursively parse
        left_tokens = tokens[:operator_index]
        right_tokens = tokens[operator_index + 1:]
        
        return ASTNode(
            type=NodeType.OPERATOR,
            operator=Operator(tokens[operator_index]),
            left=self._parse_expression(left_tokens),
            right=self._parse_expression(right_tokens)
        )