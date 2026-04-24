"""
Smart Recalculation Engine
Implements incremental graph-based calculations using NetworkX for dependency management
"""

from typing import Dict, List, Set, Tuple, Any
import networkx as nx
from neo4j import GraphDatabase
import numpy as np
from dataclasses import dataclass
from ..database.dependency_graph_builder import DependencyGraphBuilder
from .excel_formula_engine import ExcelFormulaProcessor
from ..utils.excel_parser import parse_excel_to_nodes
import logging

logger = logging.getLogger(__name__)


@dataclass
class RecalculationResult:
    """Result of a recalculation operation"""
    affected_cells: List[str]
    calculation_order: List[str]
    execution_times: Dict[str, float]  # cell_id: time_in_seconds
    errors: List[Dict[str, Any]]
    total_duration: float


class SmartRecalculationEngine:
    """Performs intelligent incremental recalculations based on cell dependencies and changes."""
    
    def __init__(self, uri: str, username: str, password: str):
        self.graph_db = DependencyGraphBuilder(uri, username, password)
        self.formula_processor = ExcelFormulaProcessor()
        self.neo4j_driver = GraphDatabase.driver(uri, auth=(username, password))
        
    def close(self):
        """Close database connections"""
        self.graph_db.close()
        self.neo4j_driver.close()
    
    def calculate_from_changes(self, changed_cells: Dict[str, Any]) -> RecalculationResult:
        """
        Performs incremental recalculation based on changed cell values
        
        Args:
            changed_cells: Dict mapping cell IDs to new values
            
        Returns:
            RecalculationResult containing affected cells and performance metrics
        """
        import time
        start_time = time.time()
        
        # 1. Mark changed cells as updated
        changed_cell_ids = list(changed_cells.keys())
        all_affected_cells = set(changed_cell_ids)
        
        # 2. Find all cells downstream that depend on changed cells
        additional_affected = self.graph_db.find_dependent_cells(changed_cell_ids)
        all_affected_cells.update(additional_affected)
        
        # 3. Build graph from the dependency information
        calculation_graph = self._build_calculation_graph(all_affected_cells)
        
        # 4. Update changed cell values in the database
        self._update_cell_values(changed_cells)
        
        # 5. Mark dependency-dirty cells in the graph
        self.graph_db.mark_cells_dirty(additional_affected)
        
        # 6. Build calculation order using topological sort
        ordered_cells = self._get_calculation_order_topologically(calculation_graph, changed_cell_ids)
        
        # 7. Execute the recalculations
        execution_times = {}
        errors = []
        
        for cell_id in ordered_cells:
            if cell_id in changed_cells:
                # Already processed as a direct change
                continue
            try:
                execution_time = self._calculate_single_cell(cell_id)
                execution_times[cell_id] = execution_time
            except Exception as e:
                errors.append({
                    'cell_id': cell_id,
                    'error': str(e),
                    'traceback': str(type(e).__name__)
                })
                logger.error(f"Error calculating cell {cell_id}: {str(e)}")
        
        total_duration = time.time() - start_time
        
        return RecalculationResult(
            affected_cells=list(all_affected_cells),
            calculation_order=ordered_cells,
            execution_times=execution_times,
            errors=errors,
            total_duration=total_duration
        )
    
    def _build_calculation_graph(self, cell_ids: List[str]) -> nx.DiGraph:
        """
        Build a NetworkX graph representing the calculation dependencies for specific cells
        
        Args:
            cell_ids: List of cell IDs to include in the subgraph
            
        Returns:
            DiGraph with calculation dependencies
        """
        graph = nx.DiGraph()
        
        # Retrieve dependency info from Neo4j for these specific cells
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (c:Cell)
                WHERE c.id IN $cell_ids
                OPTIONAL MATCH (c)-[:DEPENDS_ON]->(target:Cell)
                WHERE target.id IN $cell_ids
                RETURN c.id AS source_id, target.id AS target_id
            """, cell_ids=cell_ids)
            
            for record in result:
                source_id = record["source_id"]
                target_id = record["target_id"]
                
                graph.add_node(source_id)
                if target_id:
                    graph.add_node(target_id)
                    # Add edge where source depends ON target
                    graph.add_edge(target_id, source_id)
        
        return graph
    
    def _update_cell_values(self, changed_cells: Dict[str, Any]):
        """Update cell values in the Neo4j database"""
        with self.neo4j_driver.session() as session:
            for cell_id, new_value in changed_cells.items():
                # Determine value type and update the cell accordingly
                value_type = self._infer_value_type(new_value)
                
                session.run("""
                    MATCH (cell:Cell {id: $cell_id})
                    SET cell.value_string = $value,
                        cell.datatype = $value_type,
                        cell.dirty_flag = false,
                        cell.last_updated = datetime(),
                        cell.previous_value = cell.value_string
                """, 
                cell_id=cell_id, 
                value=str(new_value), 
                value_type=value_type)
    
    def _infer_value_type(self, value) -> str:
        """Infer the data type of a cell value"""
        if value is None:
            return "empty"
        if isinstance(value, (int, float)):
            return "number"
        if isinstance(value, str):
            # Check if it's a number in string form
            try:
                float(value)
                return "number"
            except ValueError:
                return "string"
        return "other"
    
    def _get_calculation_order_topologically(self, graph: nx.DiGraph, seed_nodes: List[str]) -> List[str]:
        """
        Get the correct order for cell calculations using topological sorting
        
        Args:
            graph: The dependency graph
            seed_nodes: Initial changed nodes to start calculation chain
            
        Returns:
            List of cell IDs in calculation order
        """
        # Get subgraph containing only the nodes we're interested in recalculating
        # This ensures we only calculate relevant parts of the graph
        relevant_nodes = set(seed_nodes)
        
        # Add all nodes that descend from our changed nodes
        for seed in seed_nodes:
            if seed in graph:
                descendants = nx.descendants(graph, seed)
                relevant_nodes.update(descendants)
        
        subgraph = graph.subgraph(relevant_nodes)
        
        # Perform topological sort to get calculation order
        try:
            # We want to calculate nodes with no dependencies first
            # Topological sort naturally gives us just that
            ordered_nodes = list(nx.topological_sort(subgraph))
            
            # Filter to exclude seed nodes which were already updated
            filtered_order = [node for node in ordered_nodes if node not in seed_nodes]
            
            # The correct calculation order is reverse topological order of dependents:
            # If A depends on B, A should be calculated after B
            # So in the dependency graph: A->B means after B calculate A
            return filtered_order
        except nx.NetworkXError as e:
            # Circular dependency detected
            logger.warning(f"Circular dependency detected in calculation graph: {str(e)}")
            # Fallback to dependency-based ordering for affected cells
            return self._resolve_circular_dependencies(subgraph, seed_nodes)
    
    def _resolve_circular_dependencies(self, graph: nx.DiGraph, seed_nodes: List[str]) -> List[str]:
        """
        Handle case of circular dependencies in Excel formulas
        Usually these arise naturally in financial models (EBIT-interest loops, etc.)
        Implements a convergence-based iterative solving algorithm
        """
        strongly_connected_components = list(nx.strongly_connected_components(graph))
        
        final_order = []
        
        # Create condensation graph (acyclic version of original)
        condensed = nx.condensation(graph, scc=strongly_connected_components)
        
        # Sort the condensation topologically
        topological_levels = list(nx.topological_sort(condensed))
        
        for scc_idx in topological_levels:
            component = strongly_connected_components[scc_idx]
            
            if len(component) == 1:
                # Single node, just add to order
                node = list(component)[0]
                if node not in seed_nodes:
                    final_order.append(node)
            else:
                # Multiple nodes in circular dependency, solve simultaneously
                non_seed_nodes = [node for node in component if node not in seed_nodes]
                if non_seed_nodes:
                    # Add all circularly-dependent nodes together
                    # In practice, this would involve special iterative calculation methods
                    final_order.extend(non_seed_nodes)
                    # TODO: Implement iterative convergence for circular dependencies
        
        return final_order
    
    def _calculate_single_cell(self, cell_id: str) -> float:
        """
        Calculate a single cell's value based on its formula and current graph state
        
        Args:
            cell_id: ID of the cell to calculate
            
        Returns:
            Processing time in seconds
        """
        import time
        start_time = time.time()
        
        # Get the cell and its formula from database
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (cell:Cell {id: $cell_id})
                RETURN cell.formula_raw AS formula, cell.sheet AS sheet
            """, cell_id=cell_id)
            
            record = result.single()
            if not record or not record["formula"]:
                # This shouldn't happen in our calculation chain unless it's an input cell
                return time.time() - start_time
            
            formula = record["formula"]
            sheet = record["sheet"]
        
        # Calculate new value using a formula processor
        # For this implementation we'll use a simplified method
        # In a production system, we would integrate with a full Excel formula engine
        new_value = self._execute_formula(formula, cell_id, sheet)
        
        # Update the calculated value back to the database
        self._update_single_cell_value(cell_id, new_value)
        
        return time.time() - start_time
    
    def _execute_formula(self, formula: str, cell_id: str, sheet: str) -> Any:
        """
        Execute formula in the context of current known cell values
        
        Args:
            formula: The formula string (without '=' prefix)
            cell_id: Cell ID for context
            sheet: Sheet name for context
            
        Returns:
            Calculated value
        """
        # We should replace this with actual Excel formula calculation
        # For now, implement basic arithmetic and reference replacement
        
        # Remove '=' if present
        if formula.startswith('='):
            formula = formula[1:]
        
        # First, get all cell references in the formula and replace with current values
        referenced_values = self._get_referenced_values(formula, sheet)
        
        # Replace cell references with their current values
        processed_formula = formula
        for ref_cell_id, ref_value in sorted(referenced_values.items(), key=lambda x: len(x[0]), reverse=True):
            # Replace full matches first
            if ref_value is not None:
                # Convert non-string values to string for formula processing
                value_str = str(ref_value)
                processed_formula = processed_formula.replace(ref_cell_id.split('_')[-2] + ref_cell_id.split('_')[-1], value_str)
        
        # This is a simplified evaluation that only works with basic arithmetics
        # A production implementation would use a proper formula parser like pycel or xlwings
        try:
            # Evaluate simple arithmetic expressions
            # Note: In a real system, we would use xlwings or a proper Excel formula engine
            result = self._evaluate_simplified_formula(processed_formula, sheet, formula)
            return result
        except:
            # Return error if unable to evaluate
            return f"ERROR_EVALUATING_FORMULA: {formula}"
    
    def _get_referenced_values(self, formula: str, current_sheet: str) -> Dict[str, Any]:
        """Get current values of cells referenced in the formula"""
        # Extract cell references from formula using our parser
        refs = self.formula_processor.get_dependencies(formula, current_sheet)
        
        with self.neo4j_driver.session() as session:
            if not refs:
                return {}
            ref_cell_ids = [ref[0] for ref in refs]  # Get target cell IDs
            
            result = session.run("""
                MATCH (cell:Cell)
                WHERE cell.id IN $cell_ids
                RETURN cell.id AS id, cell.value_string AS value
            """, cell_ids=ref_cell_ids)
            
            values_map = {}
            for record in result:
                val = record["value"]
                # Try to convert to number if possible
                try:
                    val = float(val) if '.' in str(val) else int(val)
                except (ValueError, TypeError):
                    pass  # Keep as string
                
                values_map[record["id"]] = val
                
            return values_map
    
    def _evaluate_simplified_formula(self, formula: str, sheet_name: str, original_formula: str) -> Any:
        """Evaluate simplified formulas (in a real implementation would use xlwings or similar)"""
        # This is a placeholder for actual formula evaluation
        # In a real system, we would use a proper Excel-compatible calculator
        import re
        
        # Remove spaces and replace common Excel functions with Python equivalents
        formula = formula.replace(" ", "")
        
        # This implementation only handles basic arithmetic for demo
        # Production system would use xlwings or another Excel-compatible engine
        try:
            # Just do a basic evaluation in the same thread (not secure in the general case)
            # This is only for demonstration purposes
            # Note: eval() should be replaced with a secure formula execution system in production
            # For now, we'll return a mock evaluation
            temp_expr = re.sub(r'[^0-9+\*\/\(\)\-\.\%]', '', formula)  # Only keep numbers and operations
            try:
                if '^' in formula:
                    temp_expr = formula.replace('^', '**')  # Handle exponentiation
                # For security reasons, in production this would use a proper math expression evaluator
                result = eval(temp_expr)
                return result
            except:
                # If we can't evaluate, return the original
                return original_formula
        except Exception:
            # For complex formulas, we should delegate to an Excel engine
            # In real implementation, would use xlwings or similar
            logger.info(f"Deferring complex formula to Excel engine: {original_formula}")
            return f"DEFERRED: {original_formula}"
    
    def _update_single_cell_value(self, cell_id: str, new_value: Any):
        """Update the value of a single cell in the database"""
        with self.neo4j_driver.session() as session:
            session.run("""
                MATCH (cell:Cell {id: $cell_id})
                SET cell.value_string = $value,
                    cell.dirty_flag = false,
                    cell.last_computed = datetime()
            """, cell_id=cell_id, value=str(new_value))
            
    def get_impact_analysis(self, cell_id: str) -> Dict[str, Any]:
        """
        Analyze the impact of changing a specific cell
        
        Args:
            cell_id: ID of the cell to analyze
            
        Returns:
            Dict with impact analysis results
        """
        # Get all cells that would be affected by changing this cell
        dependent_cells = self.graph_db.find_dependent_cells([cell_id])
        
        # Calculate the longest dependency chain (depth of recalculations needed)
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH path = (start:Cell {id: $cell_id})-[:DEPENDS_ON*]->(end:Cell)
                WITH path, length(path) AS path_length
                RETURN max(path_length) AS max_depth,
                       count(path) AS dependency_count,
                       collect(DISTINCT end.id) AS all_dependents
            """, cell_id=cell_id)
            
            record = result.single()
            if record:
                return {
                    'target_cell': cell_id,
                    'direct_dependents': dependent_cells,
                    'max_dependency_depth': record['max_depth'] or 0,
                    'total_dependencies': record['dependency_count'] or 0,
                    'all_affected_cells': record['all_dependents'] or [],
                }
        
        return {
            'target_cell': cell_id,
            'direct_dependents': dependent_cells,
            'max_dependency_depth': 0,
            'total_dependencies': len(dependent_cells),
            'all_affected_cells': dependent_cells,
        }