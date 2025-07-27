#!/usr/bin/env python3
"""Test script to verify FIBO ontology and LangGraph implementation."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

def test_imports():
    """Test that all new modules can be imported."""
    try:
        from app.models.fibo_ontology import FIBOLegalEntity, FIBOEquityInstrument, FIBOOntologyMapping
        from app.services.fibo_service import FIBOService
        from app.services.langgraph_service import LangGraphService
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

def test_fibo_models():
    """Test FIBO model creation."""
    try:
        from app.models.fibo_ontology import FIBOLegalEntity
        from datetime import datetime
        
        entity = FIBOLegalEntity(
            id="test-entity",
            name="Test Entity",
            legal_name="Test Legal Entity",
            legal_jurisdiction="US-NY",
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        print(f"✓ FIBO entity created: {entity.name}")
        return True
    except Exception as e:
        print(f"✗ FIBO model error: {e}")
        return False

def test_langgraph_node():
    """Test LangGraph node instantiation."""
    try:
        from app.services.langgraph_service import FIBOPositionMappingNode
        
        node = FIBOPositionMappingNode()
        print(f"✓ LangGraph node created: {node.name}")
        return True
    except Exception as e:
        print(f"✗ LangGraph node error: {e}")
        return False

if __name__ == "__main__":
    print("Testing FIBO ontology and LangGraph implementation...")
    
    tests = [
        test_imports,
        test_fibo_models,
        test_langgraph_node,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    if all(results):
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print(f"\n✗ {len([r for r in results if not r])} tests failed")
        sys.exit(1)
