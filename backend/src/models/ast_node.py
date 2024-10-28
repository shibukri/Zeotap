from enum import Enum
from typing import Optional, Union, Dict
from pydantic import BaseModel

class NodeType(str, Enum):
    OPERATOR = "operator"
    OPERAND = "operand"
    COMPARISON = "comparison"

class Operator(str, Enum):
    AND = "AND"
    OR = "OR"
    GT = ">"
    LT = "<"
    EQ = "="
    GTE = ">="
    LTE = "<="

class ASTNode(BaseModel):
    type: NodeType
    operator: Optional[Operator] = None
    left: Optional[Union['ASTNode', None]] = None
    right: Optional[Union['ASTNode', None]] = None
    field: Optional[str] = None
    value: Optional[Union[str, int, float]] = None

    class Config:
        arbitrary_types_allowed = True

    def to_dict(self) -> Dict:
        result = {
            "type": self.type,
            "operator": self.operator,
            "field": self.field,
            "value": self.value
        }
        if self.left:
            result["left"] = self.left.to_dict()
        if self.right:
            result["right"] = self.right.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: Dict) -> 'ASTNode':
        if data.get("left"):
            data["left"] = cls.from_dict(data["left"])
        if data.get("right"):
            data["right"] = cls.from_dict(data["right"])
        return cls(**data)