"""
Enhanced Financial Visualization and AI Analysis Module
Adds visualization capabilities and advanced AI analysis for the financial model
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from ..utils.llm_integration import SimpleLLMInterface
import json
from datetime import datetime


class FinancialVisualizer:
    """
    Class for generating various types of financial visualizations
    """
    
    def __init__(self):
        pass
    
    def create_income_statement_chart(self, data: List[Dict[str, Any]], title: str = "Income Statement") -> go.Figure:
        """
        Create visualization for income statement data
        """
        df = pd.DataFrame(data)
        
        fig = go.Figure()
        
        # Add different income statement components 
        if 'revenue' in df.columns:
            fig.add_trace(go.Bar(name='Revenue', x=df.get('period', df.index), y=df['revenue'], 
                               marker_color='green', opacity=0.7))
        if 'expenses' in df.columns:
            fig.add_trace(go.Bar(name='Expenses', x=df.get('period', df.index), y=df['expenses'], 
                               marker_color='red', opacity=0.7))
        if 'net_income' in df.columns:
            fig.add_trace(go.Scatter(name='Net Income', x=df.get('period', df.index), y=df['net_income'],
                                   mode='lines+markers', line=dict(color='blue', width=3)))
        
        fig.update_layout(
            title=title,
            xaxis_title="Period",
            yaxis_title="Amount",
            barmode='group',
            height=500
        )
        
        return fig
    
    def create_balance_sheet_heatmap(self, data: List[Dict[str, Any]], title: str = "Balance Sheet") -> go.Figure:
        """
        Create heatmap visualization for balance sheet data
        """
        df = pd.DataFrame(data)
        
        if not df.empty:
            # Create a pivot if we have categories
            categories = df.columns.tolist()
            values = df.values.T
            
            fig = px.imshow(
                values,
                labels=dict(x="Period", y="Category", color="Value"),
                x=list(df.index) if 'period' not in df.columns else df['period'].tolist(),
                y=categories,
                color_continuous_scale='RdBu',
                title=title
            )
        else:
            fig = go.Figure()
            fig.add_annotation(text="No data available for visualization", 
                              xref="paper", yref="paper", showarrow=False)
        
        return fig
    
    def create_cash_flow_sankey(self, data: Dict[str, Any], title: str = "Cash Flow Diagram") -> go.Figure:
        """
        Create Sankey diagram for cash flow visualization
        """
        # Example data structure for cash flow sankey
        sources = data.get('sources', [])
        targets = data.get('targets', [])
        values = data.get('values', [])
        
        # Convert labels to indices
        unique_nodes = list(set(sources + targets))
        node_indices = {label: idx for idx, label in enumerate(unique_nodes)}
        
        if len(node_indices) > 0:
            source_indices = [node_indices[s] for s in sources]
            target_indices = [node_indices[t] for t in targets]
            
            fig = go.Figure(data=[go.Sankey(
                arrangement="snap",
                node={
                    "pad": 15,
                    "thickness": 20,
                    "line": {"color": "black", "width": 0.5},
                    "label": unique_nodes
                },
                link={
                    "source": source_indices,
                    "target": target_indices, 
                    "value": values
                })])
            fig.update_layout(title_text=title, font_size=10)
        else:
            fig = go.Figure()
            fig.add_annotation(text="Insufficient data for Sankey diagram", 
                              xref="paper", yref="paper", showarrow=False)
        
        return fig
    
    def create_correlation_matrix(self, financial_metrics: Dict[str, List[float]], title: str = "Correlation Matrix") -> go.Figure:
        """
        Create correlation matrix for financial metrics
        """
        df = pd.DataFrame(financial_metrics)
        corr_matrix = df.corr()
        
        fig = px.imshow(
            corr_matrix,
            text_auto=True,
            aspect="auto",
            title=title,
            color_continuous_scale='RdBu',
            range=[-1, 1]
        )
        
        return fig
    
    def create_trend_analysis(self, data: List[Dict[str, Any]], 
                             metrics: List[str], 
                             title: str = "Trend Analysis") -> go.Figure:
        """
        Create trend analysis chart for specified metrics
        """
        df = pd.DataFrame(data)
        fig = go.Figure()
        
        for metric in metrics:
            if metric in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.get('period', df.index),
                    y=df[metric],
                    mode='lines+markers',
                    name=metric
                ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Period",
            yaxis_title="Value",
            hovermode='x'
        )
        
        return fig


class DeepAIAnalyzer:
    """
    Performs advanced AI analysis using LLM on financial data
    """
    
    def __init__(self):
        self.llm_interface = SimpleLLMInterface()
        
    def analyze_financial_health(self, financial_ratios: Dict[str, float]) -> Dict[str, Any]:
        """
        Analyze overall financial health based on financial ratios
        """
        if not self.llm_interface.enabled:
            return {"error": "LLM analyzer inactive - check configuration"}
        
        prompt = f"""
        Perform a comprehensive financial health assessment based on the following ratios:

        {json.dumps(financial_ratios, indent=2)}

        Provide analysis in the following structure:
        1. Liquidity Position
        2. Solvency Position  
        3. Profitability Position
        4. Efficiency Position
        5. Overall Risk Assessment
        6. Recommendations for Improvement
        """
        
        try:
            response = self.llm_interface.query_financial_knowledge(prompt, financial_ratios)
            return {
                "analysis": response,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"Financial health analysis failed: {str(e)}"}
    
    def forecast_future_trends(self, historical_data: List[Dict[str, Any]], 
                              prediction_period: int = 5) -> Dict[str, Any]:
        """
        Forecast future financial trends using historical data
        """
        if not self.llm_interface.enabled:
            return {"error": "LLM analyzer inactive - check configuration"}
        
        formatted_history = json.dumps(historical_data[-12:], indent=2)  # Only use most recent 12 periods
        
        prompt = f"""
        Based on the following historical financial data, predict the next {prediction_period} periods of values.
        
        Historical Data:
        {formatted_history}

        Include in the analysis:
        1. Revenue projections with uncertainty bands
        2. Expense projections with rationale  
        3. Risk factors for forecast accuracy
        4. Assumptions underlying the forecast
        """
        
        try:
            response = self.llm_interface.query_financial_knowledge(prompt, {})
            return {
                "forecast_analysis": response,
                "prediction_period": prediction_period,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"Forecasting analysis failed: {str(e)}"}
    
    def detect_anomalies(self, financial_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect potential anomalies in financial data
        """
        if not self.llm_interface.enabled:
            return {"error": "LLM analyzer inactive - check configuration"}
        
        formatted_data = json.dumps(financial_data[-6:], indent=2)  # Recent 6 periods
        
        prompt = f"""
        Review the following financial data for potential anomalies or irregularities.

        Financial Data:
        {formatted_data}

        Identify:
        1. Significant deviations from historical patterns
        2. Unusual fluctuations in key metrics
        3. Potential warning signs or red flags
        4. Areas that require further investigation
        """
        
        try:
            response = self.llm_interface.query_financial_knowledge(prompt, {})
            return {
                "anomaly_analysis": response,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"Anomaly detection failed: {str(e)}"}
    
    def generate_scenario_analysis(self, base_model: Dict[str, Any], 
                                 scenarios: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        Generate scenario analysis based on different financial assumptions
        """
        if not self.llm_interface.enabled:
            return {"error": "LLM analyzer inactive - check configuration"} 
        
        base_str = json.dumps(base_model, indent=2)
        scenarios_str = json.dumps(scenarios, indent=2)
        
        prompt = f"""
        Perform a scenario analysis using the base financial model and specified scenarios.
        
        Base Model:
        {base_str}
        
        Scenarios:
        {scenarios_str}
        
        For each scenario, explain:
        1. What changes from the base case
        2. Impact on key financial metrics
        3. Risk level of scenario
        4. Business implications of changes
        """ 
        
        try:
            response = self.llm_interface.query_financial_knowledge(prompt, {})
            return {
                "scenario_analysis": response,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"Scenario analysis failed: {str(e)}"}
    
    def summarize_complex_data(self, complex_financial_data: Any) -> Dict[str, Any]:
        """
        Create a concise summary of complex financial data
        """
        if not self.llm_interface.enabled:
            return {"error": "LLM analyzer inactive - check configuration"}
        
        # Convert complex data to JSON for better understanding
        try:
            data_str = json.dumps(complex_financial_data, indent=2, default=str)
        except:
            data_str = str(complex_financial_data)
        
        prompt = f"""
        Create a clear, concise summary of the following complex financial data. 
        Focus on the key insights, major trends, and important metrics:

        {data_str[:4000]}  # Limit input size to avoid exceeding API limits
        """
        
        try:
            response = self.llm_interface.query_financial_knowledge(prompt, {})
            return {
                "executive_summary": response,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"Summarization failed: {str(e)}"}


class FinancialVisualizationAnalyzerCombo:
    """
    Combined class that ties financial visualization with advanced AI analysis
    """
    
    def __init__(self):
        self.visualizer = FinancialVisualizer()
        self.analyzer = DeepAIAnalyzer()
        
    def generate_complete_report(self, 
                               financial_data: List[Dict],
                               ratios: Optional[Dict] = None,
                               metrics: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate a complete financial report with visualizations and AI analysis
        """
        # Generate visualizations
        charts = {}
        
        if metrics:
            charts['trend_analysis'] = self.visualizer.create_trend_analysis(
                financial_data, metrics
            ).to_json()
        
        # Add default visualizations if needed
        if 'revenue' in [c for d in financial_data for c in d.keys()] or \
           'net_income' in [c for d in financial_data for c in d.keys()]:
            charts['income_statement'] = self.visualizer.create_income_statement_chart(
                financial_data
            ).to_json()
        
        # Perform advanced analyses
        analysis_results = {}
        
        if ratios:
            analysis_results['financial_health'] = self.analyzer.analyze_financial_health(ratios)
        
        if len(financial_data) > 4:  # Need some history for analysis
            analysis_results['anomalies'] = self.analyzer.detect_anomalies(financial_data)
            analysis_results['summary'] = self.analyzer.summarize_complex_data(financial_data)
        
        return {
            "visualizations": charts,
            "ai_analyses": analysis_results,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "data_points": len(financial_data)
            }
        }