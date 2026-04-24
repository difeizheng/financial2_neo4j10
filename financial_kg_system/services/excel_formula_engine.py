"""
Excel Formula Engine Module
Handles parsing and processing of Excel formulas with various reference types
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ReferenceType(Enum):
    ABSOLUTE = "absolute"           # $A$1
    SEMI_ABSOLUTE_COL = "semi_absolute_col"  # $A1
    SEMI_ABSOLUTE_ROW = "semi_absolute_row"  # A$1
    RELATIVE = "relative"           # A1
    RANGE_ABSOLUTE = "range_absolute"         # $A$1:$B$2
    RANGE_MIXED = "range_mixed"             # A$1:$B2
    CROSS_SHEET = "cross_sheet"             # Sheet1!A1 or Sheet1.$A$1:$B$2


@dataclass
class CellReference:
    """Represents a single cell or range reference"""
    sheet: Optional[str]
    col_start: str
    row_start: int
    col_end: Optional[str] = None
    row_end: Optional[int] = None
    ref_type: ReferenceType = None

    @property
    def is_range(self) -> bool:
        return self.col_end is not None or self.row_end is not None

    def __str__(self):
        sheet_part = f"{self.sheet}!" if self.sheet else ""
        start = f"{self.col_start}{self.row_start}"
        end_part = f":${self.col_end}${self.row_end}" if self.is_range and self.col_end and self.row_end else ""
        return f"{sheet_part}{start}{end_part}"


class FormulaParser:
    """Parses Excel formulas and extracts cell references"""
    
    def __init__(self):
        # Pattern for matching different reference types
        self.ref_pattern = re.compile(
            r"([A-Za-z0-9_\.\u4e00-\u9fa5]+!)?([$]?[A-Z]+[$]?\d+)(:[$]?[A-Z]+[$]?\d+)?",
            re.IGNORECASE
        )
        
    def extract_references(self, formula: str) -> List[CellReference]:
        """Extract all cell references from a formula"""
        if not formula or formula.startswith('='):
            formula = formula[1:]  # Remove leading = if present
            
        references = []
        for match in self.ref_pattern.finditer(formula):
            full_match = match.group(0)
            sheet_part = match.group(1)
            start_part = match.group(2)
            range_part = match.group(3)
            
            # Parse sheet name
            sheet_name = None
            if sheet_part:
                sheet_name = sheet_part.rstrip('!')
                
            # Parse start cell
            start_ref = self._parse_single_reference(start_part)
            
            # Initialize CellReference
            cell_ref = CellReference(
                sheet=sheet_name,
                col_start=start_ref['col'],
                row_start=start_ref['row']
            )
            
            # Parse range end if present
            if range_part:
                end_ref = self._parse_single_reference(range_part[1:])  # Skip ':'
                cell_ref.col_end = end_ref['col']
                cell_ref.row_end = end_ref['row']
                cell_ref.ref_type = ReferenceType.RANGE_ABSOLUTE
            else:
                cell_ref.ref_type = start_ref['type']
                
            references.append(cell_ref)
            
        return references

    def _parse_single_reference(self, ref: str) -> Dict:
        """Parse a single cell reference like $A$1, A$1, $A1, A1"""
        # Remove $ symbols temporarily to extract letters and numbers
        clean_ref = ref.replace('$', '')
        col_part = ''
        row_part = ''
        
        # Separate letters (column) from digits (row)
        for char in clean_ref:
            if char.isalpha():
                col_part += char
            elif char.isdigit():
                row_part += char
                
        row_num = int(row_part) if row_part else 0
        
        # Determine reference type based on presence of $ symbols
        has_dollar_before_col = '$' in ref and ref[0] == '$'
        has_dollar_before_row = '$' in ref and f'${row_part}' in ref
        
        if has_dollar_before_col and has_dollar_before_row:
            ref_type = ReferenceType.ABSOLUTE
        elif has_dollar_before_col and not has_dollar_before_row:
            ref_type = ReferenceType.SEMI_ABSOLUTE_COL
        elif not has_dollar_before_col and has_dollar_before_row:
            ref_type = ReferenceType.SEMI_ABSOLUTE_ROW
        else:
            ref_type = ReferenceType.RELATIVE
            
        return {
            'col': col_part.upper(),
            'row': row_num,
            'type': ref_type
        }
        
    def get_reference_type(self, ref_string: str) -> Optional[ReferenceType]:
        """Determine the reference type for a single reference string"""
        parsed = self._parse_single_reference(ref_string)
        return parsed['type']


class ExcelFormulaProcessor:
    """Main processor for Excel formulas with dependency tracking"""
    
    def __init__(self):
        self.parser = FormulaParser()
        
    def get_dependencies(self, formula: str, current_sheet: str) -> List[Tuple[str, str]]:
        """
        Get all dependencies from a formula
        Returns list of (referenced_cell_id, dependency_type) tuples
        """
        references = self.parser.extract_references(formula)
        dependencies = []
        
        for ref in references:
            # Generate cell IDs based on sheet and coordinates
            if ref.is_range:
                # Handle range dependencies (e.g., sum of range)
                for col_idx in range(_col_to_num(ref.col_start), _col_to_num(ref.col_end) + 1):
                    for row_idx in range(ref.row_start, ref.row_end + 1):
                        target_sheet = ref.sheet if ref.sheet else current_sheet
                        col_str = _num_to_col(col_idx)
                        target_id = f"{target_sheet}_{row_idx}_{col_str}"
                        dependencies.append((target_id, "range_dependent"))
            else:
                # Handle single cell dependency
                target_sheet = ref.sheet if ref.sheet else current_sheet
                target_id = f"{target_sheet}_{ref.row_start}_{ref.col_start}"
                dependencies.append((target_id, "direct_dependent"))
                
        return dependencies


def _col_to_num(col: str) -> int:
    """Convert Excel column letter to number (A=1, B=2, ..., Z=26, AA=27, ...)"""
    num = 0
    for c in col.upper():
        num = num * 26 + (ord(c) - ord('A') + 1)
    return num


def _num_to_col(n: int) -> str:
    """Convert number to Excel column letter"""
    result = ""
    while n > 0:
        n -= 1
        result = chr(n % 26 + ord('A')) + result
        n //= 26
    return result