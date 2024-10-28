# test/test_rules.py
import pytest
from src.models.database import Database, Rule

@pytest.mark.asyncio
async def test_create_rule(test_db):
    database = Database("postgres", "sqlite+aiosqlite:///:memory:")
    
    # Connect to the test database
    await database.connect()
    
    rule = Rule(name="Test Rule", description="A test rule", rule_string="x > 5", ast={})
    
    # Create rule
    created_rule = await database.create_rule(rule)
    assert created_rule.id is not None
    assert created_rule.name == "Test Rule"
    
    # Get rule
    fetched_rule = await database.get_rule(created_rule.id)
    assert fetched_rule is not None
    assert fetched_rule.name == created_rule.name

    # List rules
    rules = await database.list_rules()
    assert len(rules) == 1
    assert rules[0].name == "Test Rule"

    # Cleanup
    await database.close()

@pytest.mark.asyncio
async def test_update_rule(test_db):
    database = Database("postgres", "sqlite+aiosqlite:///:memory:")
    await database.connect()
    
    rule = Rule(name="Update Rule", description="A rule to update", rule_string="x < 10", ast={})
    created_rule = await database.create_rule(rule)
    
    updated_rule = Rule(name="Updated Rule", description="Updated description", rule_string="x < 15", ast={})
    result = await database.update_rule(created_rule.id, updated_rule)
    
    assert result.name == "Updated Rule"
    assert result.description == "Updated description"
    
    await database.close()
