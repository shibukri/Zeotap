from typing import Dict, Any
from ..models.ast_node import ASTNode, NodeType, Operator
from ..utils.exceptions import RuleEvaluationError

class RuleEvaluator:
    def evaluate(self, node: ASTNode, data: Dict[str, Any]) -> bool:
        if node.type == NodeType.OPERATOR:
            if not node.operator:
                raise RuleEvaluationError("Operator node must have an operator")
                
            left_result = self.evaluate(node.left, data) if node.left else False
            right_result = self.evaluate(node.right, data) if node.right else False
            
            if node.operator == Operator.AND:
                return left_result and right_result
            elif node.operator == Operator.OR:
                return left_result or right_result
            else:
                raise RuleEvaluationError(f"Unknown operator: {node.operator}")
                
        elif node.type == NodeType.COMPARISON:
            if not node.field or node.field not in data:
                raise RuleEvaluationError(f"Field not found in data: {node.field}")
                
            field_value = data[node.field]
            
            # Type checking
            if not isinstance(field_value, (int, float, str)):
                raise RuleEvaluationError(f"Unsupported data type for field {node.field}")
                
            if not node.operator:
                raise RuleEvaluationError("Comparison node must have an operator")
                
            # Perform comparison
            if node.operator == Operator.GT:
                return field_value > node.value
            elif node.operator == Operator.LT:
                return field_value < node.value
            elif node.operator == Operator.EQ:
                return field_value == node.value
            elif node.operator == Operator.GTE:
                return field_value >= node.value
            elif node.operator == Operator.LTE:
                return field_value <= node.value
            else:
                raise RuleEvaluationError(f"Unknown comparison operator: {node.operator}")
                
        else:
            raise RuleEvaluationError(f"Unknown node type: {node.type}")