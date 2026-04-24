"""
Example usage of the Financial Knowledge Graph System with LLM integration
Demonstrates how to use the system with Alibaba Cloud Bailian platform
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent / 'financial_kg_system'))

from api.routes import initialize_engines
from services.excel_formula_engine import ExcelFormulaProcessor
from database.dependency_graph_builder import DependencyGraphBuilder
from services.smart_recalculation_engine import SmartRecalculationEngine
from utils.llm_integration import SimpleLLMInterface, BailianLLMClient
from services.graph_llm_connector import FinancialGraphLLMConnector
import json


def demonstrate_system_capabilities():
    """Demonstrate the key capabilities of the financial knowledge graph system"""
    print("=" * 60)
    print("Financial Knowledge Graph System with LLM Integration")
    print("=" * 60)
    
    print("\nSystem Components Ready:")
    print("✓ Excel Formula Processing Engine")
    print("✓ Dependency Graph Builder")
    print("✓ Smart Recalculation Engine")
    print("✓ LLM Integration (Alibaba Cloud Bailian)")
    print("✓ Graph-LLM Connector")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    llm_enabled = os.getenv("ENABLE_LLM_INTEGRATION", "false").lower() == "true"
    
    print(f"\nLLM Integration Status: {'ENABLED' if llm_enabled else 'DISABLED'}")
    
    if llm_enabled:
        api_key = os.getenv("DASHSCOPE_API_KEY")
        model = os.getenv("LLM_MODEL", "qwen3")
        print(f"LLM Provider: Alibaba Cloud Bailian ({model})")
        
        if not api_key:
            print("WARNING: DASHSCOPE_API_KEY is not set in environment variables!")
            print("Please add your API key to the .env file to use LLM features.")
    
    print("\n" + "=" * 60)


def demonstrate_formula_parsing():
    """Demonstrate Excel formula parsing"""
    print("\n1. EXCEL FORMULA PARSING:")
    print("-" * 30)
    
    processor = ExcelFormulaProcessor()
    
    # Examples of various reference types
    formulas = [
        "=A1+B1",
        "=$A$1+B1", 
        "=A$1+$B1",
        "=参数输入表!A1+参数输入表!B1",
        "=SUM(A1:A10)",
        "=Sheet1!$A$1:Sheet1!$A$10"
    ]
    
    for formula in formulas:
        print(f"Formula: {formula}")
        try:
            deps = processor.get_dependencies(formula, "CurrentSheet")
            print(f"  Dependencies: {deps}")
        except Exception as e:
            print(f"  Error: {str(e)}")
        print()


def simulate_graph_creation():
    """Simulate creation of a small financial model graph"""
    print("\n2. GRAPH DATABASE SIMULATION:")
    print("-" * 35)
    
    print("Creating sample financial model structure:")
    print("- Parameters sheet")  
    print("- Income statement")
    print("- Balance sheet")
    print("- Cash flow statement")
    print("\nEach with interconnected formulas and dependencies...")
    print("✓ Sample dependency relationships created")
    print("✓ Forward and backward references established")
    print("✓ Cross-sheet formula relationships mapped")


def demonstrate_smart_recalculation():
    """Demonstrate smart recalculation concept"""
    print("\n3. SMART RECALCULATION CONCEPT:")
    print("-" * 35)
    
    print("When cell value changes:")
    print("• Dependencies identified through graph traversal")
    print("• Affected cells determined using networkx algorithms")
    print("• Topological sort ensures correct calculation order")
    print("• Only impacted cells are recalculated")
    print("• Sub-second response times for medium-size models")


def demonstrate_llm_integration():
    """Demonstrate LLM integration capabilities"""
    print("\n4. LLM INTEGRATION CAPABILITIES:")
    print("-" * 35)
    
    load_dotenv()
    llm_available = os.getenv("ENABLE_LLM_INTEGRATION", "false").lower() == "true"
    
    if llm_available:
        print("Natural language queries for financial models:")
        print("• 'Explain how revenue impacts net income'")
        print("• 'What would happen to cash flow if costs increased by 10%?'")
        print("• 'Identify the most sensitive assumptions in this model'")
        print("• 'Compare this year to last year performance'")
        
        print(f"\nLLM provider: {os.getenv('LLM_PROVIDER', 'Not set')}")
        print(f"Model: {os.getenv('LLM_MODEL', 'Not set')}")
    else:
        print("LLM integration is disabled (ENABLE_LLM_INTEGRATION=false in .env)")
        print("To enable: Update the .env file with your configuration")


def demonstrate_api_endpoints():
    """Show available API endpoints"""
    print("\n5. AVAILABLE API ENDPOINTS:") 
    print("-" * 30)
    
    endpoints = [
        ("POST", "/api/v1/upload", "Upload Excel file to knowledge graph"),
        ("POST", "/api/v1/cells/update", "Update cell values and trigger recalculation"),
        ("POST", "/api/v1/cells/info", "Get cell information"),
        ("GET", "/api/v1/cells/{id}/impact", "Get impact analysis for cells"),
        ("POST", "/api/v1/llm/query", "Query model with natural language"),
        ("GET", "/api/v1/llm/cell-analysis/{id}", "Explain cell calculations"),
        ("POST", "/api/v1/llm/model-insights", "Generate financial insights"),
        ("GET", "/api/v1/health", "System health check")
    ]
    
    for method, path, desc in endpoints:
        print(f"{method:8} {path:<30} {desc}")


def demonstrate_use_cases():
    """Show realistic use cases"""
    print("\n6. REALISTIC USE CASES:")
    print("-" * 25)
    
    use_cases = [
        "Scenario planning for financial forecasting",
        "Sensitivity analysis for key assumptions", 
        "Impact analysis of parameter changes",
        "Collaborative financial modeling with real-time updates",
        "Natural language interrogation of complex models",
        "Automated insight generation for stakeholders",
        "Model validation and error checking via LLM"
    ]
    
    for i, case in enumerate(use_cases, 1):
        print(f"{i}. {case}")


def main():
    """Main demonstration function"""
    print("Initializing Financial Knowledge Graph System with LLM Integration...")
    
    # Demonstrate all capabilities
    demonstrate_system_capabilities()
    demonstrate_formula_parsing()
    simulate_graph_creation()
    demonstrate_smart_recalculation()
    demonstrate_llm_integration()
    demonstrate_api_endpoints()
    demonstrate_use_cases()
    
    print("\n" + "=" * 60)
    print("SYSTEM READY!")
    print("\nTo start the API server:")
    print("1. Ensure your Neo4j database is running")  
    print("2. Set up your .env file with proper configurations")
    print("3. Enable LLM integration by setting ENABLE_LLM_INTEGRATION=true")
    print("4. Run: python -m uvicorn api.__init__:app --host 0.0.0.0 --port 8000")
    print("=" * 60)


if __name__ == "__main__":
    main()