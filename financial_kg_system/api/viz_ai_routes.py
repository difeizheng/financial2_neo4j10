"""
API Endpoints for Enhanced Visualization and AI Analysis 
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from plotly.graph_objects import Figure
import json
import tempfile
import os

from ..services.visualization_ai_analyzer import FinancialVisualizationAnalyzerCombo, FinancialVisualizer, DeepAIAnalyzer

# Create router for visualization and AI endpoints
viz_ai_router = APIRouter()

# Pydantic models for request/response
class FinancialDataRequest(BaseModel):
    """Request model for financial visualization and analysis"""
    financial_data: List[Dict[str, Any]]
    ratios: Optional[Dict[str, float]] = None
    metrics: Optional[List[str]] = None
    chart_type: str = "income_statement"  # Supported: income_statement, balance_sheet, cash_flow, correlation, trend

class ScenarioAnalysisRequest(BaseModel):
    """Request model for scenario analysis"""
    base_model: Dict[str, Any]
    scenarios: List[Dict[str, float]]

class VisualizationAIComboRequest(BaseModel):
    """Request model for complete visualization and AI combination"""
    financial_data: List[Dict[str, Any]]
    ratios: Optional[Dict[str, float]] = None
    metrics: Optional[List[str]] = None

# Models to return chart data
class ChartResponse(BaseModel):
    """Response model for chart data"""
    chart_json: str  # JSON representation of the plotly figure
    chart_type: str
    success: bool

class AnalysisResponse(BaseModel):
    """Response model for AI analysis"""
    analysis_result: Dict[str, Any]
    success: bool

class CompleteReportResponse(BaseModel):
    """Response model for complete report with viz and AI"""
    success: bool
    visualizations: Dict[str, str]  # Chart JSON strings
    ai_analyses: Dict[str, Any]
    metadata: Dict[str, Any]

# Initialize the combo analyzer
combo_service = FinancialVisualizationAnalyzerCombo()


@viz_ai_router.post("/visualize", response_model=ChartResponse)
async def create_visualization(request: FinancialDataRequest):
    """Create financial visualization"""
    try:
        visualizer = FinancialVisualizer()
        
        # Create the relevant chart based on chart_type
        if request.chart_type == "income_statement":
            fig = visualizer.create_income_statement_chart(
                request.financial_data
            )
        elif request.chart_type == "balance_sheet":
            fig = visualizer.create_balance_sheet_heatmap(
                request.financial_data
            )
        elif request.chart_type == "cash_flow":
            fig = visualizer.create_cash_flow_sankey(
                {
                    "sources": [str(d) for d in request.financial_data[:5]],
                    "targets": [str(d) for d in request.financial_data[5:10]],
                    "values": [abs(hash(str(d))) % 1000 for d in request.financial_data[:5]]
                }
            )
        elif request.chart_type == "correlation":
            # Create a financial metrics dictionary for correlation
            financial_metrics = {}
            for datum in request.financial_data:
                for key, value in datum.items():
                    if isinstance(value, (int, float)):
                        if key not in financial_metrics:
                            financial_metrics[key] = []
                        financial_metrics[key].append(value) 
            fig = visualizer.create_correlation_matrix(financial_metrics)
        elif request.chart_type == "trend":
            if not request.metrics:
                # Default to first numeric columns
                first_datum = request.financial_data[0] if request.financial_data else {}
                metrics = [k for k, v in first_datum.items() if isinstance(v, (int, float))]
                request.metrics = metrics[:3]  # Limited to 3 metrics max
            fig = visualizer.create_trend_analysis(
                request.financial_data, request.metrics or []
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported chart type: {request.chart_type}")
        
        # Convert to JSON
        chart_json = fig.to_json()
        
        return ChartResponse(
            chart_json=chart_json,
            chart_type=request.chart_type,
            success=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Visualization failed: {str(e)}")


@viz_ai_router.post("/analyze/health", response_model=AnalysisResponse)
async def analyze_financial_health(ratios: Dict[str, float]):
    """Analyze financial health based on key ratios"""
    try:
        analyzer = DeepAIAnalyzer()
        result = analyzer.analyze_financial_health(ratios)
        
        return AnalysisResponse(
            analysis_result=result,
            success=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Financial health analysis failed: {str(e)}")


@viz_ai_router.post("/analyze/anomalies", response_model=AnalysisResponse)
async def detect_anomalies(financial_data: List[Dict[str, Any]]):
    """Detect anomalies in financial data"""
    try:
        analyzer = DeepAIAnalyzer()
        result = analyzer.detect_anomalies(financial_data)
        
        return AnalysisResponse(
            analysis_result=result,
            success=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anomaly detection failed: {str(e)}")


@viz_ai_router.post("/analyze/forecasts", response_model=AnalysisResponse)
async def forecast_trends(request: List[Dict[str, Any]]):
    """Forecast future financial trends"""
    try:
        analyzer = DeepAIAnalyzer()
        # Use first 5 periods as the default forecast horizon
        result = analyzer.forecast_future_trends(request, prediction_period=5)
        
        return AnalysisResponse(
            analysis_result=result,
            success=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecasting failed: {str(e)}")


@viz_ai_router.post("/analyze/scenario", response_model=AnalysisResponse)
async def perform_scenario_analysis(request: ScenarioAnalysisRequest):
    """Perform scenario analysis based on different financial assumptions"""
    try:
        analyzer = DeepAIAnalyzer()
        result = analyzer.generate_scenario_analysis(
            request.base_model,
            request.scenarios
        )
        
        return AnalysisResponse(
            analysis_result=result,
            success=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scenario analysis failed: {str(e)}")


@viz_ai_router.post("/report/generate", response_model=CompleteReportResponse)
async def generate_complete_report(request: VisualizationAIComboRequest):
    """Generate a complete financial report with visualizations and AI analysis"""
    try:
        result = combo_service.generate_complete_report(
            request.financial_data,
            request.ratios,
            request.metrics
        )
        
        return CompleteReportResponse(
            success=True,
            **result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@viz_ai_router.post("/summarize", response_model=AnalysisResponse)
async def summarize_financial_data(financial_data: List[Dict[str, Any]]):
    """Create a summary of complex financial data"""
    try:
        analyzer = DeepAIAnalyzer()
        result = analyzer.summarize_complex_data(financial_data)
        
        return AnalysisResponse(
            analysis_result=result,
            success=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")