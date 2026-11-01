"""
Rich Text Flattener (Rule L5, L6)
Flattens myScheme slate/plate rich text ASTs into numbered lines of plain text,
preserving list items, table structures, and paragraph boundaries.
"""

import html
import re
from typing import Any, Dict, List, Tuple


def clean_line_text(text: str) -> str:
    """Collapses whitespace and strips leading/trailing space."""
    if not text:
        return ""
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def flatten_rich_text(content: Any) -> Tuple[List[str], str]:
    """
    Transforms arbitrary slate/plate rich text JSON AST or raw strings
    into a list of cleaned lines and an aggregate string.
    """
    if not content:
        return [], ""

    if isinstance(content, str):
        cleaned = clean_line_text(content)
        return ([cleaned] if cleaned else []), cleaned

    lines: List[str] = []

    def extract_nodes(node: Any) -> None:
        if isinstance(node, str):
            cleaned = clean_line_text(node)
            if cleaned:
                lines.append(cleaned)
            return

        if isinstance(node, list):
            for child in node:
                extract_nodes(child)
            return

        if isinstance(node, dict):
            node_type = node.get("type", "")

            # Table row handling
            if node_type == "table_row":
                cells = []
                for cell in node.get("children", []):
                    cell_text = "".join(get_leaf_text(cell))
                    cleaned_cell = clean_line_text(cell_text)
                    if cleaned_cell:
                        cells.append(cleaned_cell)
                if cells:
                    lines.append(" | ".join(cells))
                return

            # Leaf nodes
            if "text" in node:
                cleaned = clean_line_text(node.get("text", ""))
                if cleaned:
                    lines.append(cleaned)
                return

            # Parent / wrapper nodes
            if "children" in node:
                extract_nodes(node["children"])

    def get_leaf_text(node: Any) -> List[str]:
        leaves = []
        if isinstance(node, dict):
            if "text" in node:
                leaves.append(node["text"])
            for child in node.get("children", []):
                leaves.extend(get_leaf_text(child))
        elif isinstance(node, list):
            for item in node:
                leaves.extend(get_leaf_text(item))
        return leaves

    extract_nodes(content)
    # Deduplicate empty lines
    filtered_lines = [l for l in lines if l]
    aggregate = "\n".join(filtered_lines)
    return filtered_lines, aggregate
