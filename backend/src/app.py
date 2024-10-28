from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import os

from src.models.ast_node import ASTNode
from src.services.rule_parser import RuleParser
from src.services.rule_evaluator import RuleEvaluator
from src.services.rule_combiner import RuleCombiner
from src.utils.exceptions import RuleParsingError, RuleEvaluationError, RuleCombiningError
from src.models.database import create_database, DatabaseInterface

# Pydantic models
class RuleBase(BaseModel):
    name: str
    description: str
    rule_string: str

class RuleCreate(RuleBase):
    pass

class Rule(RuleBase):
    id: str
    ast: Dict[str, Any]

    class Config:
        from_attributes = True

class RuleEvaluation(BaseModel):
    data: Dict[str, Any]

class RuleEvaluationResponse(BaseModel):
    rule_id: str
    rule_name: str
    result: bool
    evaluated_data: Dict[str, Any]

class CombineRules(BaseModel):
    rule_ids: List[str]
    strategy: str = Field(default="AND", description="Combination strategy (AND/OR)")

class CombinedRuleResponse(BaseModel):
    combined_ast: Dict[str, Any]
    rule_ids: List[str]
    strategy: str

class HealthResponse(BaseModel):
    status: str
    database_type: str
    version: str

# Initialize FastAPI app
app = FastAPI(
    title="Rule Engine API",
    description="A rule engine for evaluating and combining business rules",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DB_TYPE = os.getenv("DB_TYPE", "mongodb")
DB_CONFIG = {
    "mongodb": os.getenv("MONGODB_URL", "mongodb://localhost:27017/"),
    "postgres": os.getenv("POSTGRES_URL", "postgresql+asyncpg://user:password@localhost/rule_engine"),
    "sqlite": os.getenv("SQLITE_PATH", "rule_engine.db")
}

# Initialize services
db: DatabaseInterface = create_database(DB_TYPE, DB_CONFIG[DB_TYPE])
parser = RuleParser()
evaluator = RuleEvaluator()
combiner = RuleCombiner()

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    try:
        await db.connect()
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    try:
        await db.close()
    except Exception as e:
        print(f"Error closing database connection: {e}")

@app.post("/rules/", response_model=Rule, tags=["Rules"])
async def create_rule(rule_create: RuleCreate):
    """Create a new rule"""
    try:
        ast = parser.parse(rule_create.rule_string)
        rule = Rule(
            name=rule_create.name,
            description=rule_create.description,
            rule_string=rule_create.rule_string,
            ast=ast.to_dict(),
            id=""  # Will be set by database
        )
        return await db.create_rule(rule)
    except RuleParsingError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating rule: {str(e)}")

@app.get("/rules/", response_model=List[Rule], tags=["Rules"])
async def list_rules(skip: int = 0, limit: int = 100):
    """List all rules with pagination"""
    try:
        return await db.list_rules(skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing rules: {str(e)}")

@app.get("/rules/{rule_id}", response_model=Rule, tags=["Rules"])
async def get_rule(rule_id: str):
    """Get a specific rule by ID"""
    rule = await db.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule

@app.post("/rules/{rule_id}/evaluate", response_model=RuleEvaluationResponse, tags=["Rules"])
async def evaluate_rule(rule_id: str, evaluation: RuleEvaluation):
    """Evaluate a rule against provided data"""
    rule = await db.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
        
    try:
        ast = ASTNode.from_dict(rule.ast)
        result = evaluator.evaluate(ast, evaluation.data)
        return RuleEvaluationResponse(
            rule_id=rule_id,
            rule_name=rule.name,
            result=result,
            evaluated_data=evaluation.data
        )
    except RuleEvaluationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error evaluating rule: {str(e)}")

@app.post("/rules/combine", response_model=CombinedRuleResponse, tags=["Rules"])
async def combine_rules(combine_request: CombineRules):
    """Combine multiple rules using the specified strategy"""
    rules = []
    for rule_id in combine_request.rule_ids:
        rule = await db.get_rule(rule_id)
        if not rule:
            raise HTTPException(
                status_code=404,
                detail=f"Rule with id {rule_id} not found"
            )
        rules.append(ASTNode.from_dict(rule.ast))
        
    try:
        combined_ast = combiner.combine_rules(rules, combine_request.strategy)
        return CombinedRuleResponse(
            combined_ast=combined_ast.to_dict(),
            rule_ids=combine_request.rule_ids,
            strategy=combine_request.strategy
        )
    except RuleCombiningError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error combining rules: {str(e)}"
        )

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint to verify service status"""
    return HealthResponse(
        status="healthy",
        database_type=DB_TYPE,
        version="1.0.0"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        log_level="info"
    )