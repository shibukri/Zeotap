# src/models/database.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, Column, String, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from motor.motor_asyncio import AsyncIOMotorClient
import aiosqlite
from bson import ObjectId
from .rule import Rule
import json
from typing import Optional

Base = declarative_base()

class SQLRule(Base):
    """SQLAlchemy Rule model"""
    __tablename__ = "rules"
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    rule_string = Column(String)
    ast = Column(JSON)

class DatabaseInterface(ABC):
    """Abstract base class for database implementations"""
    
    @abstractmethod
    async def connect(self):
        pass
    
    @abstractmethod
    async def close(self):
        pass
    
    @abstractmethod
    async def create_rule(self, rule: Rule) -> Rule:
        pass
    
    @abstractmethod
    async def get_rule(self, rule_id: str) -> Optional[Rule]:
        pass
    
    @abstractmethod
    async def list_rules(self, skip: int = 0, limit: int = 100) -> List[Rule]:
        pass

class MongoDBDatabase(DatabaseInterface):
    """MongoDB implementation"""
    
    def __init__(self, url: str):
        self.url = url
        self.client = None
        self.db = None
    
    async def connect(self):
        self.client = AsyncIOMotorClient(self.url)
        self.db = self.client.rule_engine
    
    async def close(self):
        if self.client:
            self.client.close()
    
    async def create_rule(self, rule: Rule) -> Rule:
        result = await self.db.rules.insert_one(rule.dict(exclude={'id'}))
        rule.id = str(result.inserted_id)
        return rule
    
    async def get_rule(self, rule_id: str) -> Optional[Rule]:
        rule_dict = await self.db.rules.find_one({"_id": ObjectId(rule_id)})
        if rule_dict:
            rule_dict['id'] = str(rule_dict.pop('_id'))
            return Rule(**rule_dict)
        return None
    
    async def list_rules(self, skip: int = 0, limit: int = 100) -> List[Rule]:
        rules = []
        cursor = self.db.rules.find().skip(skip).limit(limit)
        async for rule_dict in cursor:
            rule_dict['id'] = str(rule_dict.pop('_id'))
            rules.append(Rule(**rule_dict))
        return rules

class PostgresDatabase(DatabaseInterface):
    """PostgreSQL implementation using SQLAlchemy"""
    
    def __init__(self, url: str):
        self.url = url
        self.engine = None
        self.session_factory = None
    
    async def connect(self):
        self.engine = create_async_engine(self.url)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.session_factory = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def close(self):
        if self.engine:
            await self.engine.dispose()
    
    async def create_rule(self, rule: Rule) -> Rule:
        async with self.session_factory() as session:
            sql_rule = SQLRule(
                name=rule.name,
                description=rule.description,
                rule_string=rule.rule_string,
                ast=rule.ast
            )
            session.add(sql_rule)
            await session.commit()
            rule.id = str(sql_rule.id)
            return rule
    
    async def get_rule(self, rule_id: str) -> Optional[Rule]:
        async with self.session_factory() as session:
            sql_rule = await session.get(SQLRule, int(rule_id))
            if sql_rule:
                return Rule(
                    id=str(sql_rule.id),
                    name=sql_rule.name,
                    description=sql_rule.description,
                    rule_string=sql_rule.rule_string,
                    ast=sql_rule.ast
                )
            return None
    
    async def list_rules(self, skip: int = 0, limit: int = 100) -> List[Rule]:
        async with self.session_factory() as session:
            sql_rules = await session.query(SQLRule).offset(skip).limit(limit).all()
            return [
                Rule(
                    id=str(sql_rule.id),
                    name=sql_rule.name,
                    description=sql_rule.description,
                    rule_string=sql_rule.rule_string,
                    ast=sql_rule.ast
                )
                for sql_rule in sql_rules
            ]

class SQLiteDatabase(DatabaseInterface):
    """SQLite implementation"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db = None
    
    async def connect(self):
        self.db = await aiosqlite.connect(self.db_path)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                rule_string TEXT NOT NULL,
                ast TEXT NOT NULL
            )
        """)
        await self.db.commit()
    
    async def close(self):
        if self.db:
            await self.db.close()
    
    async def create_rule(self, rule: Rule) -> Rule:
        cursor = await self.db.execute(
            """
            INSERT INTO rules (name, description, rule_string, ast)
            VALUES (?, ?, ?, ?)
            """,
            (rule.name, rule.description, rule.rule_string, str(rule.ast))
        )
        await self.db.commit()
        rule.id = str(cursor.lastrowid)
        return rule
    
    # async def get_rule(self, rule_id: str) -> Optional[Rule]:
    #     cursor = await self.db.execute(
    #         "SELECT * FROM rules WHERE id = ?",
    #         (int(rule_id),)
    #     )
    #     row = await cursor.fetchone()
    #     if row:
    #         return Rule(
    #             id=str(row[0]),
    #             name=row[1],
    #             description=row[2],
    #             rule_string=row[3],
    #             ast=eval(row[4])  # Note: Use json.loads in production
    #         )
    #     return None
    async def get_rule(self, rule_id: str) -> Optional[Rule]:
        async with self.db.execute(
            "SELECT * FROM rules WHERE id = ?",
            (int(rule_id),)  # Ensure this matches your id type
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return Rule(
                    id=str(row[0]),
                    name=row[1],
                    description=row[2],
                    rule_string=row[3],
                    ast=json.loads(row[4])  # Safely parse the AST
                )
        return None
    
    async def list_rules(self, skip: int = 0, limit: int = 100) -> List[Rule]:
        cursor = await self.db.execute(
            "SELECT * FROM rules LIMIT ? OFFSET ?",
            (limit, skip)
        )
        rows = await cursor.fetchall()
        return [
            Rule(
                id=str(row[0]),
                name=row[1],
                description=row[2],
                rule_string=row[3],
                ast=eval(row[4])  # Note: Use json.loads in production
            )
            for row in rows
        ]

# Factory function to create database instance
def create_database(db_type: str, connection_string: str) -> DatabaseInterface:
    """
    Factory function to create appropriate database instance
    
    Args:
        db_type: Type of database ('mongodb', 'postgres', or 'sqlite')
        connection_string: Database connection string
    
    Returns:
        DatabaseInterface: Instance of appropriate database class
    """
    if db_type == "mongodb":
        return MongoDBDatabase(connection_string)
    elif db_type == "postgres":
        return PostgresDatabase(connection_string)
    elif db_type == "sqlite":
        return SQLiteDatabase(connection_string)
    else:
        raise ValueError(f"Unsupported database type: {db_type}")