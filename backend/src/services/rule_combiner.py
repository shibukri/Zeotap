from typing import List, Dict, Counter, Set
from collections import Counter
from ..models.ast_node import ASTNode, NodeType, Operator
from ..utils.exceptions import RuleCombiningError

class RuleCombiner:
    def combine_rules(self, rules: List[ASTNode], strategy: str = "AND") -> ASTNode:
        if not rules:
            raise RuleCombiningError("No rules to combine")
            
        if len(rules) == 1:
            return rules[0]
            
        if strategy == "AND" or strategy == "OR":
            return self._combine_with_operator(rules, 
                                            Operator.AND if strategy == "AND" else Operator.OR)
        elif strategy == "OPTIMIZE":
            return self._optimize_combination(rules)
        else:
            raise RuleCombiningError(f"Unknown combination strategy: {strategy}")

    def _combine_with_operator(self, rules: List[ASTNode], operator: Operator) -> ASTNode:
        result = rules[0]
        for rule in rules[1:]:
            result = ASTNode(
                type=NodeType.OPERATOR,
                operator=operator,
                left=result,
                right=rule
            )
        return result

    def _analyze_node(self, node: ASTNode, operator_count: Counter, 
                     comparison_groups: Dict[str, List[ASTNode]], visited: Set[int] = None):
        if visited is None:
            visited = set()
            
        # Avoid circular references
        node_id = id(node)
        if node_id in visited:
            return
        visited.add(node_id)

        if node.type == NodeType.OPERATOR:
            operator_count[node.operator] += 1
            if node.left:
                self._analyze_node(node.left, operator_count, comparison_groups, visited)
            if node.right:
                self._analyze_node(node.right, operator_count, comparison_groups, visited)
        elif node.type == NodeType.COMPARISON and node.field:
            if node.field not in comparison_groups:
                comparison_groups[node.field] = []
            comparison_groups[node.field].append(node)

    def _optimize_combination(self, rules: List[ASTNode]) -> ASTNode:
        operator_count = Counter()
        comparison_groups: Dict[str, List[ASTNode]] = {}
        
        # Analyze all rules
        for rule in rules:
            self._analyze_node(rule, operator_count, comparison_groups)
        
        # Optimize common field comparisons
        optimized_nodes = []
        
        # Group comparisons by field
        for field, comparisons in comparison_groups.items():
            if len(comparisons) > 1:
                # Combine comparisons with OR if they're for the same field
                optimized_nodes.append(self._combine_with_operator(comparisons, Operator.OR))
            else:
                optimized_nodes.extend(comparisons)
        
        # If we have any nodes that weren't part of field groups, add them
        remaining_nodes = [rule for rule in rules if not any(
            id(rule) == id(node) for node in sum(comparison_groups.values(), [])
        )]
        optimized_nodes.extend(remaining_nodes)
        
        # Use most common operator for final combination
        most_common_op = operator_count.most_common(1)[0][0] if operator_count else Operator.AND
        
        return self._combine_with_operator(optimized_nodes, most_common_op)

    def simplify_ast(self, node: ASTNode) -> ASTNode:
        """Simplifies the AST by removing redundant nodes and combining similar operations"""
        if not node:
            return node
            
        if node.type == NodeType.OPERATOR:
            node.left = self.simplify_ast(node.left)
            node.right = self.simplify_ast(node.right)
            
            # Simplify nested operators of the same type
            if (node.left and node.left.type == NodeType.OPERATOR and 
                node.left.operator == node.operator):
                node = self._flatten_operator(node)
                
        return node

    def _flatten_operator(self, node: ASTNode) -> ASTNode:
        """Flattens nested operators of the same type"""
        if not node or node.type != NodeType.OPERATOR:
            return node
            
        nodes = self._collect_same_operator_nodes(node)
        return self._combine_with_operator(nodes, node.operator)

    def _collect_same_operator_nodes(self, node: ASTNode) -> List[ASTNode]:
        """Collects all nodes connected by the same operator"""
        if not node or node.type != NodeType.OPERATOR:
            return [node]
            
        nodes = []
        if node.left:
            if (node.left.type == NodeType.OPERATOR and 
                node.left.operator == node.operator):
                nodes.extend(self._collect_same_operator_nodes(node.left))
            else:
                nodes.append(node.left)
                
        if node.right:
            if (node.right.type == NodeType.OPERATOR and 
                node.right.operator == node.operator):
                nodes.extend(self._collect_same_operator_nodes(node.right))
            else:
                nodes.append(node.right)
                
        return nodes