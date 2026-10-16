"""
Zero-Shot Pydantic Structured Output Engine for Milli-Scrapes.
Extracts strongly typed Pydantic models from DOM trees and clean Markdown.
Supports nested models, lists, type coercion, and validation error handling.
"""

import re
import json
from typing import Type, TypeVar, Optional, Any, Dict, List
from pydantic import BaseModel, ValidationError
from bs4 import BeautifulSoup

T = TypeVar("T", bound=BaseModel)


class PydanticExtractor:
    """
    Extracts and validates structured data into Pydantic models.
    """

    @classmethod
    def extract_from_html(
        cls,
        html: str,
        model_cls: Type[T],
        css_selectors: Optional[Dict[str, str]] = None
    ) -> Optional[T]:
        """
        Extracts fields from HTML using optional selector hints or smart heuristic matching,
        validating the output strictly against the target Pydantic model.
        """
        soup = BeautifulSoup(html, "html.parser")
        extracted_fields: Dict[str, Any] = {}

        # 1. Use CSS selectors if explicitly mapped
        if css_selectors:
            for field_name, selector in css_selectors.items():
                if field_name in model_cls.model_fields:
                    nodes = soup.select(selector)
                    if not nodes:
                        extracted_fields[field_name] = None
                    elif len(nodes) == 1:
                        extracted_fields[field_name] = nodes[0].get_text(strip=True)
                    else:
                        extracted_fields[field_name] = [n.get_text(strip=True) for n in nodes]

        # 2. Heuristic extraction for remaining missing fields
        for field_name, field_info in model_cls.model_fields.items():
            if field_name in extracted_fields and extracted_fields[field_name] is not None:
                continue

            # Check meta tags
            meta = soup.find("meta", property=re.compile(rf".*{field_name}.*", re.I)) or \
                   soup.find("meta", attrs={"name": re.compile(rf".*{field_name}.*", re.I)})
            if meta and meta.get("content"):
                extracted_fields[field_name] = meta["content"].strip()
                continue

            # Check title
            if field_name in ("title", "name", "headline"):
                h1 = soup.find(["h1", "title"])
                if h1:
                    extracted_fields[field_name] = h1.get_text(strip=True)
                    continue

            # Check common class or id attributes
            node = soup.find(attrs={"id": re.compile(rf"^{field_name}$", re.I)}) or \
                   soup.find(attrs={"class": re.compile(rf"^{field_name}$", re.I)})
            if node:
                extracted_fields[field_name] = node.get_text(strip=True)

        try:
            return model_cls.model_validate(extracted_fields)
        except ValidationError:
            # Attempt to instantiate with partial fields or default values
            try:
                # Filter None values to allow field defaults
                filtered = {k: v for k, v in extracted_fields.items() if v is not None}
                return model_cls.model_validate(filtered)
            except Exception:
                return None

    @classmethod
    def get_json_schema(cls, model_cls: Type[BaseModel]) -> Dict[str, Any]:
        """Returns JSON schema representation of the model for LLM prompting."""
        return model_cls.model_json_schema()
