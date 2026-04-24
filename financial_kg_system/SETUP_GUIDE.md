"""
Financial Knowledge Graph System - Setup and Usage Guide

This system integrates Excel financial modeling, Neo4j knowledge graphs, and Alibaba Cloud Bailian LLM capabilities 
to create a powerful platform for financial analysis.
"""

print("=" * 80)
print("FINANCIAL KNOWLEDGE GRAPH SYSTEM")
print("Integrated Solution with Excel, Neo4j and Alibaba Cloud Bailian LLM")
print("=" * 80)

print("\n📁 PROJECT STRUCTURE:")
print("""
financial_kg_system/
├── api/
│   ├── __init__.py          # Main API application (FastAPI)
│   └── routes.py           # API route definitions
├── data/                   # For data files (input/output)
├── database/
│   └── dependency_graph_builder.py  # Neo4j graph management
├── models/                 # ML models (if needed)
├── services/
│   ├── excel_formula_engine.py     # Excel formula parsing
│   ├── smart_recalculation_engine.py # Recalculation engine
│   └── graph_llm_connector.py     # Integration between graph and LLM
├── utils/
│   ├── cache_manager.py     # Redis and NetworkX caching
│   ├── excel_parser.py     # Excel file processing
│   └── llm_integration.py  # LLM integration utilities
├── tests/
│   └── integration_tests.py # System tests
├── .env                    # Environment configuration
├── main.py                # Main application entry point
├── requirements.txt       # Python dependencies
├── README.md             # System documentation
└── ARCHITECTURE.md       # Architecture documentation
""")

print("\n🚀 QUICK START GUIDE:")
print("""
1. SETUP ENVIRONMENT:
   - Copy the provided configuration from .env to your environment
   - Update the DASHSCOPE_API_KEY with your Alibaba Cloud key
   - Set ENABLE_LLM_INTEGRATION=true if you want LLM features

2. INSTALL DEPENDENCIES:
   pip install -r requirements.txt

3. START SERVICES:
   - Start your Neo4j database server
   - Start your Redis server (optional but recommended)

4. UPDATE CONFIGURATION:
   Edit the .env file with your specific settings:
   - Neo4j connection details
   - Redis settings
   - LLM API configuration for Bailian

5. VERIFY INSTALLATION:
   Run: python example_usage.py
""")

print("\n☁️  ALIBABA CLOUD BAILIAN INTEGRATION:")
print("""
The system provides seamless integration with Alibaba Cloud's Bailian platform:

1. GET YOUR API KEY:
   - Log in to Alibaba Cloud Console (https://home.console.aliyun.com/)
   - Navigate to DashScope (https://dashscope.console.aliyun.com/)
   - Go to API Key Management and create a new API key

2. CONFIGURE API INTEGRATION:
   In .env file:
   - LLM_PROVIDER=aliyun-bailian
   - DASHSCOPE_API_KEY=your_actual_api_key_here
   - LLM_MODEL=qwen3  # Or other supported models
   - ENABLE_LLM_INTEGRATION=true

3. SUPPORTED QWEN MODELS:
   - qwen3 (newest version)
   - qwen-max (for complex tasks)
   - qwen-plus (balanced)
   - qwen-turbo (fast response)

4. LLM CAPABILITIES:
   - Natural language queries:
     "Explain how revenue affects net income in this model"
   - Financial insight generation:
     "Analyze trends in the cash flow statement"
   - Formula validation:
     "Check if there are any errors in these financial formulas"
""")

print("\n📊 EXCEL TO GRAPH CONVERSION PROCESS:")
print("""
The system follows these steps when processing Excel files:

1. PARSE FORMULAS - Recognize all reference types:
   - Absolute: $A$1, $I$250
   - Semi-absolute: $A1, A$1
   - Cross-sheet: Sheet1!$A$1
   - Ranges: A1:B10

2. MAP DEPENDENCIES - Create relationships in Neo4j:
   - (Cell)-[:DEPENDS_ON]->(Target_Cell)
   - (Worksheet)-[:CONTAINS_CELL]->(Cell)

3. BUILD CALCULATION GRAPH:
   - Directed acyclic graph (DAG) for proper calculation order
   - Handle circular references appropriately

4. ENABLE INTELLIGENT RECALCULATION:
   - Only affected cells are re-evaluated
   - Topological sort ensures correct dependency order
""")

print("\n🔗 KEY API ENDPOINTS:")
endpoints = [
    ("/api/v1/upload", "POST", "Upload Excel file to convert to knowledge graph"),
    ("/api/v1/cells/update", "POST", "Update cell values and trigger smart recalculation"),
    ("/api/v1/cells/info", "POST", "Retrieve cell information by ID"),
    ("/api/v1/cells/{id}/impact", "GET", "Analyze impact of changes on specific cell"),
    ("/api/v1/llm/query", "POST", "Natural language query of financial model"),
    ("/api/v1/llm/model-insights", "POST", "Generate financial insights using LLM"),
    ("/api/v1/health", "GET", "Health check of system components")
]

for path, method, desc in endpoints:
    print(f"   {method:9} {path:25} - {desc}")

print("\n⚙️  ADVANCED CONFIGURATION OPTIONS:")
print("""
DATABASE:
- Configure connection pool settings for high load
- Set up cluster topology for Neo4j Enterprise
- Consider APOC library installation for advanced graph capabilities

CACHE:
- Adjust TTL values for your data refresh requirements
- Scale horizontally with Redis Cluster
- Consider using different cache strategies based on use patterns

LLM INTEGRATION:
- Fine-tune temperature and other model parameters
- Implement rate limiting to manage API usage
- Secure API keys with proper IAM controls
- Consider different models for different types of queries
""")

print("\n🔍 TYPICAL WORKFLOW EXAMPLES:")
examples = [
    "Import a complex financial model with multiple sheets and cross-sheet references",
    "Change a key parameter and trigger automatic cascading recalculation",
    "Perform what-if analysis using natural language queries",
    "Generate management reports showing sensitivity to key assumptions",
    "Monitor impact of changes across different modules of the financial model"
]

for i, example in enumerate(examples, 1):
    print(f"   {i}. {example.capitalize()}")

print("\n🛡️  SECURITY CONSIDERATIONS:")
security_items = [
    "Validate and sanitize all Excel inputs to prevent malicious formulas",
    "Use proper authentication for API endpoints (not implemented in this basic version)",
    "Keep LLM credentials secure and consider using credential rotation",
    "Implement proper access controls for sensitive financial data",
    "Log all access to sensitive financial models for audit purposes"
]

for item in security_items:
    print(f"   ✓ {item}")

print("\n" + "=" * 80)
print("SYSTEM CAPABILITIES SUMMARY:")
print("✓ Full Excel formula compatibility")
print("✓ Bidirectional cell dependency tracking") 
print("✓ Real-time incremental recalculation")
print("✓ Scalable graph database backend (Neo4j)")
print("✓ High-performance caching layer")
print("✓ Natural language interface (via Bai Lian)")
print("✓ Comprehensive API coverage")
print("✓ End-to-end financial model understanding")
print("=" * 80)

print(f"\nTo start the API server:")
print(f"   python -m uvicorn api.__init__:app --host 0.0.0.0 --port 8000")
print(f"\nTo run example usage:")
print(f"   python example_usage.py")
print()