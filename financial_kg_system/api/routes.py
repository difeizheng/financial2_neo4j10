"""
API Layer for Financial Knowledge Graph System
Implements FastAPI endpoints for interacting with the financial model
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from ..services.smart_recalculation_engine import SmartRecalculationEngine, RecalculationResult
from ..database.dependency_graph_builder import DependencyGraphBuilder
from ..services.graph_llm_connector import FinancialGraphLLMConnector
from ..utils.excel_parser import parse_excel_to_nodes
from .viz_ai_routes import viz_ai_router
import json
import tempfile
import os
from pathlib import Path

# Create router instance
router = APIRouter()

# Global engine instance (typically handled with dependency injection in production)
engine: Optional[SmartRecalculationEngine] = None
llm_connector: Optional[FinancialGraphLLMConnector] = None


# Pydantic models for request/response
class CellUpdateRequest(BaseModel):
    """Request model for updating cell values"""
    cell_updates: Dict[str, Any]  # Maps cell_id to new value
    trigger_recalculation: bool = True


class CellQueryRequest(BaseModel):
    """Request model for querying cell information"""
    cell_ids: List[str]


class CalculationResultResponse(BaseModel):
    """Response model for calculation results"""
    success: bool
    affected_cells: List[str]
    calculation_order: List[str]
    execution_times: Dict[str, float]
    errors: List[Dict[str, Any]]
    total_duration: float
    message: Optional[str] = None


class CellInfoResponse(BaseModel):
    """Response model for cell information"""
    cell_id: str
    value: Optional[str]
    formula: Optional[str]
    cell_type: str
    datatype: str
    dependencies: List[Dict[str, Any]]
    dependents: List[Dict[str, Any]]
    worksheet_name: str


class NaturalQueryRequest(BaseModel):
    query: str
    context_cell_ids: Optional[List[str]] = None


class LLMAnalysisResponse(BaseModel):
    success: bool
    response: str
    model_used: Optional[str] = None
    provider: Optional[str] = None


def initialize_engines():
    """Initialize the engine and LLM connector"""
    global engine, llm_connector
    # These should come from configuration in production
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    
    engine = SmartRecalculationEngine(neo4j_uri, neo4j_user, neo4j_password)
    # Initialize LLM connector with the same graph instance
    if engine.graph_db:
        llm_connector = FinancialGraphLLMConnector(engine.graph_db)


@router.post("/upload", response_model=dict)
async def upload_excel(file: UploadFile = File(...)):
    """Upload an Excel file and import it into the knowledge graph"""
    global engine
    
    if not engine:
        initialize_engines()
    
    if not engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    
    try:
        # Save uploaded file temporarily
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, file.filename)
        
        with open(temp_file_path, 'wb') as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process the Excel file and import to knowledge graph
        workbook_data = parse_excel_to_nodes(temp_file_path)
        
        # Import data into Neo4j
        model_id = engine.graph_db.import_workbook_structure(workbook_data)
        
        # Clean up temp file
        os.remove(temp_file_path)
        os.rmdir(temp_dir)
        
        return {
            "success": True,
            "model_id": model_id,
            "message": f"Successfully imported {len(workbook_data)} cells from {file.filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process Excel file: {str(e)}")


@router.post("/cells/update", response_model=CalculationResultResponse)
async def update_cells(request: CellUpdateRequest):
    """Update one or more cells and trigger recalculation"""
    global engine
    
    if not engine:
        initialize_engines()
    
    if not engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    
    try:
        # Use the SmartRecalculationEngine to perform updates and recalculation
        result = engine.calculate_from_changes(request.cell_updates)
        
        return CalculationResultResponse(
            success=True,
            affected_cells=result.affected_cells,
            calculation_order=result.calculation_order,
            execution_times=result.execution_times,
            errors=result.errors,
            total_duration=result.total_duration
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update cells: {str(e)}")


@router.post("/cells/info", response_model=List[CellInfoResponse])
async def get_cell_info(request: CellQueryRequest):
    """Fetch detailed information about one or more cells"""
    global engine
    
    if not engine:
        initialize_engines()
    
    if not engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    
    try:
        results = []
        for cell_id in request.cell_ids:
            cell_details = engine.graph_db.get_cell_details(cell_id) 
            
            if cell_details:
                cell_info = CellInfoResponse(
                    cell_id=cell_id,
                    value=cell_details.get('value_string'),
                    formula=cell_details.get('formula_raw'),
                    cell_type=cell_details.get('cell_type', ''),
                    datatype=cell_details.get('datatype', ''),
                    dependencies=cell_details.get('dependencies', []),
                    dependents=cell_details.get('dependents', []),
                    worksheet_name=cell_details.get('worksheet_name', '')
                )
                results.append(cell_info)
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch cell info: {str(e)}")


@router.get("/cells/{cell_id}/impact", response_model=Dict[str, Any])
async def get_impact_analysis(cell_id: str):
    """Get impact analysis for a specific cell (which cells are affected by it)"""
    global engine
    
    if not engine:
        initialize_engines()
    
    if not engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    
    try:
        impact_analysis = engine.get_impact_analysis(cell_id)
        return impact_analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze impact: {str(e)}")


@router.post("/llm/query", response_model=LLMAnalysisResponse)
async def natural_language_query(request: NaturalQueryRequest):
    """Query the financial model using natural language"""
    global llm_connector
    
    if not llm_connector:
        initialize_engines()
    
    if not llm_connector:
        raise HTTPException(status_code=500, detail="LLM connector not initialized")
    
    try:
        if request.context_cell_ids:
            # Analyze specific cells
            result = llm_connector.analyze_cell_relationships(request.context_cell_ids)
        else:
            # Answer general query
            result = llm_connector.answer_natural_query(request.query)
        
        return LLMAnalysisResponse(
            success=True,
            response=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM query failed: {str(e)}")


@router.get("/llm/cell-analysis/{cell_id}", response_model=LLMAnalysisResponse)
async def explain_calculation_chain(cell_id: str):
    """Get LLM explanation of how a specific cell is calculated"""
    global llm_connector
    
    if not llm_connector:
        initialize_engines()
    
    if not llm_connector:
        raise HTTPException(status_code=500, detail="LLM connector not initialized")
    
    try:
        result = llm_connector.explain_calculation_chain(cell_id)
        return LLMAnalysisResponse(
            success=True,
            response=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM analysis failed: {str(e)}")


@router.post("/llm/model-insights", response_model=dict)
async def generate_model_insights(sheet_name: Optional[str] = None):
    """Generate insights about the financial model using LLM"""
    global llm_connector
    
    if not llm_connector:
        initialize_engines()
    
    if not llm_connector:
        raise HTTPException(status_code=500, detail="LLM connector not initialized")
    
    try:
        result = llm_connector.generate_insights(sheet_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM insights generation failed: {str(e)}")


# Include the enhanced visualization and AI analysis endpoints
router.include_router(viz_ai_router, prefix="/vizai", tags=["visualization-ai-analysis"])


@router.get("/health", response_model=dict)
async def health_check():
    """Health check endpoint"""
    global engine
    
    if not engine:
        initialize_engines()
    
    if not engine:
        return {"status": "error", "details": "Engine not initialized"}
    
    try:
        # Try to perform a simple DB operation to verify connection
        with engine.neo4j_driver.session() as session:
            result = session.run("RETURN 1")
            single = result.single()
            if single:
                return {"status": "healthy", "database_connection": True}
            else:
                return {"status": "error", "database_connection": False}
    except Exception as e:
        return {"status": "error", "details": str(e)}


@router.get("/", response_model=dict)
async def root():
    """Root endpoint with system info"""
    return {
        "message": "Financial Model Knowledge Graph System API",
        "status": "running",
        "modules": [
            "Excel Formula Engine",
            "Dependency Graph Builder", 
            "Smart Recalculation Engine",
            "LLM Integration",
            "Advanced Visualization and AI Analysis"
        ]
    }


# In a production system, we would include additional endpoints for:
# - Getting calculation lineage
# - Version control of models
# - Audit logs
# - Exporting results
# - Running scenarios
# But these basic endpoints cover core functionality