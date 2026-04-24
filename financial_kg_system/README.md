# Excel Financial Model Knowledge Graph System

A sophisticated system that transforms traditional Excel-based financial models into a dynamic knowledge graph stored in Neo4j, enabling complex dependency tracking, real-time recalculation, and powerful querying capabilities. Now includes integration with large language models for natural language interaction with financial data (supports Alibaba Cloud Bailian platform) and advanced visualizations and AI analysis capabilities.

## Overview

Traditional Excel-based financial models often become difficult to maintain as they grow in complexity. This system addresses these challenges by:
- Converting Excel models to a graph structure in Neo4j
- Maintaining and visualizing dependencies between cells
- Performing intelligent, incremental recalculations
- Providing REST API access to the financial model and its calculations
- Implementing a dual-layer cache system for optimal performance
- Enabling natural language queries and analysis through LLM integration
- Supporting visualization of financial data and advanced AI analysis

## Architecture Components

### Core Services

#### 1. Excel Formula Engine
Handles parsing and processing of Excel formulas with various reference types:
- **Absolute references:** `$A$1`
- **Semi-absolute references:** `$A1` or `A$1`
- **Range references:** `$A$1:$B$2`
- **Cross-sheet references:** `Sheet1!A1`

#### 2. Dependency Graph Builder
Converts Excel cells and their relationships into Neo4j graph structures:
- **Node Types:** `:Cell`, `:Worksheet`, `:Formula`
- **Relationships:** `:DEPENDS_ON`, `:CONTAINS_CELL`, `:HAS_FORMULA`
- Optimized schema for performance with complex financial models

#### 3. Smart Recalculation Engine
Features an incremental recalculation using NetworkX for dependency management:
- **Topological Sorting:** Determines the correct calculation order based on dependencies
- **Cycle Detection:** Handles circular dependencies appropriately with iterative algorithms
- **Performance Optimization:** Only recalculates affected cells in the proper sequence

#### 4. LLM Integration
Integrates with large language models for natural language queries:
- **Supported Providers:** Alibaba Cloud Bailian (DashScope API), with extensible architecture for more
- **Capabilities:** Natural language questions about financial models, model validation, insight generation
- **Safety:** Configurable access and proper API key handling

#### 5. Visualization & Deep AI Analysis
New capabilities for financial insights and analysis:
- **Visualization:** Interactive charts including income statements, balance sheets, trend analysis and correlations
- **AI Analysis:** Advanced financial analysis including health assessment, anomaly detection, forecasting, and scenario modeling
- **Report Generation:** Automated report creation with visualizations and AI-driven insights

#### 6. Cache Management Layer
Implements a dual-cache strategy:
- **Redis Cache:** Distributed cache for shared access and persistence
- **NetworkX Cache:** In-memory graph caching for faster dependency operations
- **Intelligent Invalidation:** Cached items have configurable TTLs that match access patterns

#### 7. API Layer
REST endpoints for interacting with the financial model:
- **Upload Endpoint:** Processes Excel files and imports them into the graph
- **Calculation Endpoint:** Updates cell values and triggers recalculation
- **Query Endpoint:** Retrieves cell information with dependencies
- **LLM Endpoints:** Natural language queries and insights
- **Visualization Endpoints:** Interactive chart generation
- **AI Analysis Endpoints:** Advanced analytics and forecasting
- **Impact Analysis:** Identifies which cells will be affected by specific changes

## Requirements

- Python 3.9+
- Neo4j 4.4+ community or enterprise edition
- Redis server (if using caching features)
- Windows/Linux/MacOS

## Installation

1. Clone the repository
2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Install Plotly and additional visualization packages:
   ```
   pip install plotly pandas kaleido
   ```
4. Start Neo4j database and Redis server
5. Set environment variables (optional, see Configuration section below)

## Configuration

Configuration is handled through the `.env` file:

```
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Redis Configuration (for caching)
REDIS_HOST=localhost
REDIS_PORT=6379

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# LLM Configuration (Alibaba Cloud Bailian)
LLM_PROVIDER=aliyun-bailian
DASHSCOPE_API_KEY=your_api_key_here  # Get this from Alibaba Cloud Console
LLM_MODEL=qwen3  # Or qwen-max, qwen-turbo
ENABLE_LLM_INTEGRATION=true  # Set to 'true' to enable LLM features

# Visualization & AI Analysis Options
ENABLE_VISUALIZATION=true  # Set to 'true' to enable charting features
```

## Usage

### Setting up LLM Integration

This system supports Alibaba Cloud's Bailian platform through their DashScope API:

1. Register at Alibaba Cloud and navigate to the DashScope Console
2. Get your API key
3. Update the `.env` file with your `DASHSCOPE_API_KEY`
4. Set `ENABLE_LLM_INTEGRATION=true` in the `.env` file
5. Select your desired model in the `LLM_MODEL` setting

### Starting the Application

1. Ensure Neo4j and Redis are running
2. Update `.env` with your configurations
3. Start the application:
   ```
   python main.py
   ```
4. The API should be accessible at `http://localhost:8000`

### Key API Endpoints

#### Standard Financial Operations:
- `POST /api/v1/upload` - Upload and import Excel file
- `POST /api/v1/cells/update` - Update cell values and trigger recalculation
- `POST /api/v1/cells/info` - Get detailed information about cells
- `GET /api/v1/cells/{cell_id}/impact` - Impact analysis for changes on specified cell

#### LLM Integration:
- `POST /api/v1/llm/query` - Natural language queries about the financial model
- `GET /api/v1/llm/cell-analysis/{cell_id}` - Explanation of how a cell is calculated
- `POST /api/v1/llm/model-insights` - Generate financial insights using LLM

#### Visualization and AI Analysis:
- `POST /api/v1/vizai/visualize` - Generate financial visualizations
- `POST /api/v1/vizai/analyze/health` - Financial health analysis
- `POST /api/v1/vizai/analyze/anomalies` - Detect anomalies in financial data
- `POST /api/v1/vizai/analyze/forecasts` - Forecast trends
- `POST /api/v1/vizai/analyze/scenario` - Perform scenario analysis
- `POST /api/v1/vizai/report/generate` - Generate comprehensive report

### Excel Model Requirements

- Only .xlsx format is currently supported
- Complex formulas are preserved and converted to graph relationships
- Cross-sheet references are fully supported

## Visualization & Deep AI Analysis Features

The system includes advanced visualization and AI analysis capabilities:

- **Interactive Charts**: Bar charts, line graphs, heatmaps, Sankey diagrams, and correlation matrices
- **AI-Powered Analyses**: Financial health scoring, forecasting, scenario planning, and anomaly detection
- **Natural Language Reports**: Generate human-readable insights from data and models
- **Predictive Modeling**: Use historical trends and AI to make predictions

## Technology Stack

- **Python**: Core implementation language
- **Neo4j**: Property graph database for storing financial models
- **NetworkX**: Graph algorithms for dependency management
- **FastAPI**: Modern web framework for building APIs
- **Redis**: Distributed caching for performance  
- **openpyxl**: Reading and parsing Excel files
- **Alibaba Cloud Bailian**: LLM integration for natural language understanding
- **Plotly**: Visualization capabilities
- **pandas**: Data manipulation for visualizations
- **pytest**: Testing framework with extensive coverage

## Performance Characteristics

- Efficient handling of Excel models with 6-50 worksheets
- Incremental recalculation - only affected cells are computed
- Dual-layer caching system optimizes for both low-latency requests and shared access
- Asymptotic scaling with model complexity through graph partitioning
- Fast chart rendering with precomputed layout algorithms

## Testing

Run the example usage to see all system capabilities:
```
python example_usage.py
```

Then run the enhanced demo to see visualization and AI analysis:
```
python enhanced_demo.py
```

## Design Philosophy

This system balances several key objectives:
1. Accurate representation of Excel models with no loss of functionality
2. High performance through graph algorithms and caching
3. Scalability from small models to complex multi-worksheet structures
4. Easy integration with existing financial modeling workflows
5. Natural language capabilities through LLM integration
6. Rich visualization and deep analysis for better financial insights
7. Auditability through impact analysis and change tracking