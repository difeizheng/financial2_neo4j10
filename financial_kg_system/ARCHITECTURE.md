# Financial Knowledge Graph System - Architecture Overview

## System Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Excel File    │───▶│  API Layer      │───▶│  Neo4j Graph    │
│  (Financial     │    │  (FastAPI)      │    │  Database       │
│  Model)         │    │                 │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  Smart Recalc.   │
                       │  Engine          │
                       │                 │
                       └──────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │ Dependency Graph │
                       │  Builder         │
                       └──────────────────┘
                              │
                              ▼
                    ┌─────────────────────────┐
                    │    Cache Manager       │
                    │  ┌─────────────────┐   │
                    │  │ NetworkX Cache  │   │
                    │  │  (In-Memory)    │   │
                    │  └─────────────────┘   │
                    │  ┌─────────────────┐   │
                    │  │ Redis Cache     │   │
                    │  │  (Distributed)  │   │
                    │  └─────────────────┘   │
                    └─────────────────────────┘
```

## Data Flow

1. **Excel Upload**: Excel files are parsed using openpyxl to extract cell values and formulas

2. **Graph Conversion**: Cell information is converted to Neo4j graph nodes and relationships via the Dependency Graph Builder

3. **API Processing**: FastAPI endpoints handle requests to update cells and query model information

4. **Recalculation**: When cells are changed, the Smart Recalculation Engine determines dependent cells and calculates new values

5. **Caching**: Both NetworkX and Redis caches store frequently accessed information and dependency graphs to improve performance

## Node Labels in Neo4j

- `:FinancialModel` - Represents an entire Excel workbook
- `:Worksheet` - Individual Excel sheets
- `:Cell` - Individual cells with properties like value, formula, type
- `:Formula` - Calculations and functions used in cells  

## Relationships in Neo4j

- `(FinancialModel)-[:CONTAINS_WORKSHEET]->(Worksheet)`
- `(Worksheet)-[:CONTAINS_CELL]->(Cell)`
- `(Cell)-[:DEPENDS_ON]->(Cell)` - Shows cell dependencies based on formulas
- `(Cell)-[:HAS_FORMULA]->(Formula)` - Links cells to their calculations

## Key Features

### 1. Dynamic Dependency Tracking
- Automatically discovers and stores relationships between cells based on formulas
- Handles cross-sheet references correctly (e.g., `Sheet1.C5`)
- Processes complex ranges (e.g., `SUM(A1:A10)`)

### 2. Incremental Recalculation
- Only recalculates cells that are affected by changes
- Uses topological sorting to determine the correct order of calculations
- Handles circular dependencies intelligently

### 3. Multi-layer Caching
- **L1 (NetworkX)**: In-memory dependency graphs for fastest access
- **L2 (Redis)**: Shared distributed cache for persistence and concurrency
- Automatic cache invalidation when data changes

### 4. Impact Analysis
- Before making changes, analyzes which cells will be affected
- Provides insights into how changes propagate through the model
- Prevents unintended consequences

## Architecture Benefits

- **Scalability**: Designed to handle Excel models with 6-50+ worksheets efficiently
- **Performance**: Uses graph algorithms and caching for quick responses
- **Maintainability**: Clear separation of concerns between components
- **Visibility**: Exposes dependency relationships and calculation paths
- **Auditability**: Logs all changes and their impacts for compliance