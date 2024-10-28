from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field
from pymongo import MongoClient
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

class Rule(BaseModel):
    id: Optional[PyObjectId] = Field(alias='_id')
    name: str
    description: Optional[str]
    rule_string: str
    ast: Dict  # Stores the AST representation
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

# MongoDB connection and schema setup
class Database:
    def __init__(self, connection_string: str):
        self.client = MongoClient(connection_string)
        self.db = self.client.rule_engine
        self.rules = self.db.rules
        
        # Create indexes
        self.rules.create_index("name", unique=True)
        self.rules.create_index("created_at")
        
    async def create_rule(self, rule: Rule) -> Rule:
        rule_dict = rule.dict(by_alias=True)
        result = self.rules.insert_one(rule_dict)
        rule.id = result.inserted_id
        return rule
    
    async def get_rule(self, rule_id: str) -> Optional[Rule]:
        rule_dict = self.rules.find_one({"_id": ObjectId(rule_id)})
        if rule_dict:
            return Rule(**rule_dict)
        return None
    
    async def list_rules(self, skip: int = 0, limit: int = 100):
        rules = self.rules.find().skip(skip).limit(limit)
        return [Rule(**rule) for rule in rules]
    
    async def update_rule(self, rule_id: str, rule: Rule) -> Optional[Rule]:
        rule_dict = rule.dict(exclude={"id"})
        rule_dict["updated_at"] = datetime.utcnow()
        result = self.rules.update_one(
            {"_id": ObjectId(rule_id)},
            {"$set": rule_dict}
        )
        if result.modified_count:
            return await self.get_rule(rule_id)
        return None
    
    async def delete_rule(self, rule_id: str) -> bool:
        result = self.rules.delete_one({"_id": ObjectId(rule_id)})
        return result.deleted_count > 0