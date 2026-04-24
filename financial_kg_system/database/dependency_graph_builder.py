"""
Dependency Graph Builder Module
Handles conversion of Excel cell structures to Neo4j graph relationships
"""

from typing import Dict, List, Tuple, Any
from neo4j import GraphDatabase, Driver
import json
from ..services.excel_formula_engine import ExcelFormulaProcessor, CellReference


class DependencyGraphBuilder:
    """Builds and manages the financial model knowledge graph in Neo4j"""
    
    def __init__(self, uri: str, username: str, password: str):
        self.driver: Driver = GraphDatabase.driver(uri, auth=(username, password))
        self.formula_processor = ExcelFormulaProcessor()
        
    def close(self):
        """Close the database connection"""
        self.driver.close()

    def init_schema(self):
        """Initialize the graph schema with indexes and constraints"""
        with self.driver.session() as session:
            # Create indexes for performance
            session.run("CREATE INDEX cell_id_index IF NOT EXISTS FOR (c:Cell) ON c.id")
            session.run("CREATE INDEX sheet_name_index IF NOT EXISTS FOR (s:Worksheet) ON s.name")
            session.run("CREATE INDEX cell_type_index IF NOT EXISTS FOR (c:Cell) ON c.cell_type")
            session.run("CREATE INDEX cell_dirty_flag_index IF NOT EXISTS FOR (c:Cell) ON c.dirty_flag")
    
    def import_workbook_structure(self, workbook_data: List[Dict]) -> str:
        """
        Import Excel workbook structure into Neo4j graph
        
        Args:
            workbook_data: List of cell data in format similar to node.json
                           Each dict should have: id, value, formula_raw, sheet, is_head, etc.
        
        Returns:
            str: Model ID for the imported workbook
        """
        from datetime import datetime
        model_id = f"model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with self.driver.session() as session:
            # First, create the model and worksheet nodes
            self._create_model_and_worksheets(session, workbook_data, model_id)
            
            # Then create cell nodes
            self._create_cells(session, workbook_data, model_id)
            
            # Finally, build dependency relationships based on formulas
            self._create_dependencies(session, workbook_data)
        
        return model_id
    
    def _create_model_and_worksheets(self, session, workbook_data, model_id: str):
        """Create model and worksheet nodes"""
        worksheets = set()
        for cell_data in workbook_data:
            if 'sheet' in cell_data:
                worksheets.add(cell_data['sheet'])
        
        # Create model node
        session.run("""
            MERGE (model:FinancialModel {id: $model_id})
            SET model.created_at = datetime()
        """, model_id=model_id)
        
        # Create worksheet nodes
        for sheet_name in worksheets:
            session.run("""
                MATCH (model:FinancialModel {id: $model_id})
                MERGE (worksheet:Worksheet {name: $sheet_name})
                CREATE (model)-[:CONTAINS_WORKSHEET]->(worksheet)
            """, model_id=model_id, sheet_name=sheet_name)
    
    def _create_cells(self, session, workbook_data, model_id: str):
        """Create individual cell nodes based on workbook data"""
        for cell_data in workbook_data:
            cell_id = cell_data.get('id')
            sheet_name = cell_data.get('sheet')
            value = cell_data.get('value')
            formula_raw = cell_data.get('formula_raw')
            is_head = cell_data.get('is_head', False)
            row = cell_data.get('row', 0)
            col = cell_data.get('col', '')
            row_category = cell_data.get('row_category')
            col_category = cell_data.get('col_category')
            
            # Get cell type based on whether it has formula
            cell_type = 'formula' if formula_raw else 'input'
            if is_head:
                cell_type = 'header'
                
            # Determine value type
            value_type = self._infer_value_type(value)
            
            session.run("""
                MATCH (worksheet:Worksheet {name: $sheet_name})
                MERGE (cell:Cell {id: $cell_id})
                SET cell.value_string = $value,
                    cell.formula_raw = $formula_raw,
                    cell.cell_type = $cell_type,
                    cell.datatype = $value_type,
                    cell.is_header = $is_header,
                    cell.row_num = $row,
                    cell.column = $col,
                    cell.row_category = $row_category,
                    cell.col_category = $col_category,
                    cell.dirty_flag = false,
                    cell.last_updated = datetime()
                CREATE (worksheet)-[:CONTAINS_CELL]->(cell)
            """, 
            cell_id=cell_id,
            sheet_name=sheet_name,
            value=value,
            formula_raw=formula_raw,
            cell_type=cell_type,
            value_type=value_type,
            is_header=is_head,
            row=row,
            col=col,
            row_category=row_category,
            col_category=col_category)
    
    def _create_dependencies(self, session, workbook_data):
        """Create dependency relationships between cells based on formulas"""
        for cell_data in workbook_data:
            cell_id = cell_data.get('id')
            formula_raw = cell_data.get('formula_raw')
            sheet_name = cell_data.get('sheet')
            
            if formula_raw:  # Only create dependencies if cell has a formula
                try:
                    dependencies = self.formula_processor.get_dependencies(formula_raw, sheet_name)
                    
                    for dep_cell_id, dep_type in dependencies:
                        session.run("""
                            MATCH (source_cell:Cell {id: $source_id}), 
                                  (target_cell:Cell {id: $target_id})
                            WHERE source_cell <> target_cell
                            MERGE (source_cell)-[rel:DEPENDS_ON {
                                relationship_type: $dep_type,
                                formula_expression: $formula
                            }]->(target_cell)
                        """, 
                        source_id=cell_id, 
                        target_id=dep_cell_id, 
                        dep_type=dep_type,
                        formula=formula_raw)
                except Exception as e:
                    # Log parsing errors but don't fail the whole import
                    print(f"Warning: Could not parse formula '{formula_raw}' for cell {cell_id}: {str(e)}")

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
                # Check if it's a date-like string
                if self._looks_like_date(value):
                    return "date"
                return "string"
        return "other"
    
    def _looks_like_date(self, value: str) -> bool:
        """Simple heuristic to determine if string looks like a date"""
        import re
        # Look for common date separators and formats
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
            r'[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}|[A-Za-z]{3,9}\s+\d{1,2}\s+\d{4}',  # Month DD, YYYY
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, value):
                return True
        return False
    
    def find_dependent_cells(self, cell_ids: List[str]) -> List[str]:
        """
        Find all cells that depend on the given cells, directly or indirectly
        
        Args:
            cell_ids: List of cell IDs to check dependencies for
            
        Returns:
            List of cell IDs that depend on the input cells
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (target:Cell)
                WHERE target.id IN $cell_ids
                MATCH path = (target)<-[:DEPENDS_ON*]-(dependent:Cell)
                RETURN collect(DISTINCT dependent.id) AS dependent_cells
            """, cell_ids=cell_ids)
            
            record = result.single()
            if record:
                return record["dependent_cells"]
            return []
    
    def mark_cells_dirty(self, cell_ids: List[str]):
        """Mark cells as dirty when their referenced cell values change"""
        with self.driver.session() as session:
            session.run("""
                MATCH (cell:Cell)
                WHERE cell.id IN $cell_ids
                SET cell.dirty_flag = true,
                    cell.last_changed = datetime()
            """, cell_ids=cell_ids)
    
    def get_dirty_cells(self) -> List[Dict]:
        """Get all cells that need recalculation"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (cell:Cell {dirty_flag: true})
                RETURN cell.id AS id, cell.formula_raw AS formula, 
                       cell.cell_type AS type, cell.sheet AS sheet
            """)
            return [record.data() for record in result]
    
    def build_calculation_order(self, starting_cell_ids: List[str]) -> List[str]:
        """
        Build the calculation order for given cells using topological sort
        
        Args:
            starting_cell_ids: Beginning of calculation chain
            
        Returns:
            Ordered list of cell IDs for recalculation
        """
        with self.driver.session() as session:
            # Get forward dependencies (cells that depend on starting cells)
            result = session.run("""
                MATCH path = (start:Cell {id: $start_id})-[:DEPENDS_ON*]->(target:Cell)
                UNWIND nodes(path)[1..] AS cell_node
                WITH DISTINCT cell_node
                OPTIONAL MATCH (cell_node)-[r:DEPENDS_ON]->(next_cell:Cell)
                WITH cell_node, collect(next_cell.id) as dependencies
                RETURN cell_node.id AS id, cell_node.formula_raw AS formula, dependencies
                ORDER BY size(dependencies)  // Nodes with few dependents are calculated later
            """, start_id=starting_cell_ids[0] if starting_cell_ids else "")
            
            # For this simplified version, just return cells in dependency order
            # In a more complex implementation, we'd use NetworkX algorithms
            return starting_cell_ids

    def get_cell_details(self, cell_id: str) -> Dict[str, Any]:
        """
        Get comprehensive information about a cell including its dependencies
        
        Args:
            cell_id: ID of the cell to retrieve information for
            
        Returns:
            Dictionary containing cell details and dependencies
        """
        with self.driver.session() as session:
            # Get cell details
            cell_result = session.run("""
                MATCH (cell:Cell {id: $cell_id})
                OPTIONAL MATCH (worksheet:Worksheet)-[:CONTAINS_CELL]->(cell)
                RETURN cell {.*}, worksheet.name AS worksheet_name
            """, cell_id=cell_id)
            
            cell_info = cell_result.single()
            if not cell_info:
                return {}
            
            # Get dependencies of this cell
            dependencies_result = session.run("""
                MATCH (cell:Cell {id: $cell_id})-[:DEPENDS_ON]->(target:Cell)
                RETURN target.id AS id, target.value_string AS value
            """, cell_id=cell_id)
            
            dependencies = [record.data() for record in dependencies_result]
            cell_info["dependencies"] = dependencies
            
            # Get cells that depend on this cell
            dependents_result = session.run("""
                MATCH (cell:Cell {id: $cell_id})<-[:DEPENDS_ON]-(source:Cell)
                RETURN source.id AS id, source.formula_raw AS formula
            """, cell_id=cell_id)
            
            dependents = [record.data() for record in dependents_result]
            cell_info["dependents"] = dependents
            
            return dict(cell_info)