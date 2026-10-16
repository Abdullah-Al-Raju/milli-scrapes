"""
Structured Data and Tabular Extractor.
Extracts HTML tables, lists, and key-value pairs into structured JSON dictionaries.
"""

import re
from html import unescape
from typing import List, Dict, Any


class StructuredDataExtractor:
    """
    Parses structured data artifacts (HTML tables, item lists, key-value grids) into pure JSON.
    """

    def extract_tables(self, html: str) -> List[List[Dict[str, str]]]:
        """
        Parses all HTML tables into lists of row dictionaries.
        """
        tables = []
        table_matches = re.findall(r"<table\b[^>]*>(.*?)<\/table>", html, flags=re.IGNORECASE | re.DOTALL)

        for tbl in table_matches:
            # Extract header columns
            headers = []
            th_matches = re.findall(r"<th\b[^>]*>(.*?)<\/th>", tbl, flags=re.IGNORECASE | re.DOTALL)
            if th_matches:
                headers = [self._clean_cell(th) for th in th_matches]

            # Extract rows
            rows_data = []
            tr_matches = re.findall(r"<tr\b[^>]*>(.*?)<\/tr>", tbl, flags=re.IGNORECASE | re.DOTALL)
            for tr in tr_matches:
                td_matches = re.findall(r"<td\b[^>]*>(.*?)<\/td>", tr, flags=re.IGNORECASE | re.DOTALL)
                if not td_matches:
                    continue
                cells = [self._clean_cell(td) for td in td_matches]

                if headers and len(cells) == len(headers):
                    row_dict = {headers[i]: cells[i] for i in range(len(cells))}
                else:
                    row_dict = {f"col_{i}": cells[i] for i in range(len(cells))}
                rows_data.append(row_dict)

            if rows_data:
                tables.append(rows_data)

        return tables

    def extract_key_values(self, html: str) -> Dict[str, str]:
        """
        Detects common key-value patterns (e.g. Price: $99, Status: Available, Seats: 4).
        """
        data = {}
        # Replace tags with newlines to separate discrete blocks
        clean = re.sub(r"<[^>]+>", "\n", html)
        clean = unescape(clean)

        for line in clean.splitlines():
            line = line.strip()
            if ":" in line:
                parts = line.split(":", 1)
                k = parts[0].strip()
                v = parts[1].strip()
                if 2 <= len(k) <= 30 and 1 <= len(v) <= 60 and len(k.split()) <= 4:
                    data[k] = v
        return data

    def _clean_cell(self, cell_html: str) -> str:
        text = re.sub(r"<[^>]+>", "", cell_html)
        return unescape(text).strip()
