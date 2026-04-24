"""
Financial Graph LLM Integration
Connects the Excel financial model knowledge graph with the LLM interface
"""

from typing import Dict, List, Optional, Any
from ..utils.llm_integration import SimpleLLMInterface
from ..database.dependency_graph_builder import DependencyGraphBuilder
import json


class FinancialGraphLLMConnector:
    """
    Connector class to link the financial graph database with LLM functionality
    """
    
    def __init__(self, graph_builder: DependencyGraphBuilder):
        """
        Initialize the connector with a graph builder instance
        
        Args:
            graph_builder: Instance of DependencyGraphBuilder
        """
        self.graph_builder = graph_builder
        self.llm_interface = SimpleLLMInterface()
        
    def analyze_cell_relationships(self, cell_ids: List[str]) -> str:
        """
        Analyze relationships between cells using LLM
        """
        if not self.llm_interface.enabled:
            return "LLM analysis unavailable - not enabled in configuration"
        
        # Get detailed cell information from the graph
        cell_details = []
        for cell_id in cell_ids:
            details = self.graph_builder.get_cell_details(cell_id)
            cell_details.append(details)
        
        if not cell_details:
            return "No cells found to analyze"
    
        context = {
            "cells_analyzed": len(cell_details),
            "cell_details": cell_details,
        }
        
        question = f"请分析这{len(cell_details)}个财务模型单元格之间的关系，解释它们如何相互影响以及可能存在的依赖。"
        response = self.llm_interface.query_financial_knowledge(question, context)
        
        return response
    
    def explain_calculation_chain(self, cell_id: str) -> str:
        """
        Explain how a specific cell is calculated, using both graph analysis and LLM
        """
        if not self.llm_interface.enabled:
            return "LLM explanation unavailable - not enabled in configuration"
        
        # Get cell information
        cell_detail = self.graph_builder.get_cell_details(cell_id)
        
        if not cell_detail or 'formula_raw' not in cell_detail or not cell_detail['formula_raw']:
            return f"Cell {cell_id} does not have a formula to explain"
        
        # Get dependency chain
        dependents = self.graph_builder.find_dependent_cells([cell_id])
        
        context = {
            "target_cell": cell_id,
            "formula": cell_detail['formula_raw'],
            "affects_cells": dependents
        }
        
        question = f"请解释单元格 {cell_id} 的计算公式: {cell_detail['formula_raw']}，并说明它的变化如何影响其他单元格"
        response = self.llm_interface.query_financial_knowledge(question, context)
        
        return response
    
    def generate_insights(self, sheet_name_or_cell_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate insights about the financial model using LLM
        """
        if not self.llm_interface.enabled:
            return {"error": "LLM insights unavailable - not enabled in configuration"}
        
        # Get relevant financial data to analyze
        # For now, we'll get a sample of cells; in practice, this would be more strategic
        with self.graph_builder.driver.session() as session:
            if sheet_name_or_cell_filter:
                result = session.run("""
                    MATCH (sheet:Worksheet {name: $sheet_name})-[:CONTAINS_CELL]->(cell:Cell)
                    RETURN cell.id as id, cell.value_string as value, cell.formula_raw as formula
                    LIMIT 20
                """, sheet_name=sheet_name_or_cell_filter)
            else:
                result = session.run("""
                    MATCH (cell:Cell)
                    WHERE cell.value_string IS NOT NULL
                    RETURN cell.id as id, cell.value_string as value, cell.formula_raw as formula
                    LIMIT 50
                """)
            
            cells_data = [{"id": record["id"], "value": record["value"], "formula": record["formula"]} 
                         for record in result]
        
        if not cells_data:
            return {"message": "No financial data found to analyze"}
        
        financial_data_str = json.dumps(cells_data, ensure_ascii=False, indent=2)[:4000]  # Limit for API
        
        insights = self.llm_interface.extract_insights(financial_data_str)
        return insights
    
    def validate_model_formulas(self) -> Dict[str, Any]:
        """
        Use LLM to validate all formulas in the financial model
        """
        if not self.llm_interface.enabled:
            return {"error": "LLM validation unavailable - not enabled in configuration"}
        
        # Get sample of formulas from the model
        with self.graph_builder.driver.session() as session:
            result = session.run("""
                MATCH (cell:Cell)
                WHERE cell.formula_raw IS NOT NULL AND cell.formula_raw <> ''
                RETURN cell.formula_raw as formula, cell.id as id
                LIMIT 100
            """)
            
            formulas = [record["formula"] for record in result if record["formula"]]
        
        if not formulas:
            return {"message": "No formulas found to validate"}
        
        validation_results = self.llm_interface.validate_formulas(formulas)
        return validation_results
    
    def answer_natural_query(self, query: str) -> str:
        """
        Answer a natural language query about the financial model
        """
        if not self.llm_interface.enabled:
            return "LLM query processing unavailable - not enabled in configuration"
        
        # The LLM interface handles the question with the appropriate context
        response = self.llm_interface.query_financial_knowledge(query, {})
        return response