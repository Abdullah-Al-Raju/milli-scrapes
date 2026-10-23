"""
Milli System 1 Decision Primitives.
Matches and extends the TypeSafe Jev & Convai Laya System 1 decision interface.
Evaluates unstructured inputs against typed constraints in a single forward pass without token-by-token generation.
"""

from typing import Dict, List, Any, Optional, TypeVar, Generic
from pydantic import BaseModel, Field

T = TypeVar("T")


class Noul(BaseModel):
    """
    Calibrated Boolean / Yes-No Probability Primitive.
    Evaluates binary conditions (e.g. 'is_paywall', 'is_blocked', 'has_pagination')
    without generating text tokens.
    """
    value: bool = Field(description="Boolean decision thresholded at 0.5")
    probability: float = Field(description="Calibrated probability in [0.0, 1.0]")
    confidence: float = Field(default=0.95, description="Confidence metric of probability estimation")
    latency_ms: float = Field(default=0.0, description="Inference latency in milliseconds")

    def __bool__(self) -> bool:
        return self.value


class Choice(BaseModel, Generic[T]):
    """
    Single-Pass Categorical Selection Primitive.
    Selects one option from a predefined candidate set alongside full probability distribution.
    """
    selected: str = Field(description="Winning category option")
    probabilities: Dict[str, float] = Field(description="Normalized probability distribution over all options")
    confidence: float = Field(default=0.95, description="Margin of victory over second-best option")
    latency_ms: float = Field(default=0.0, description="Inference latency in milliseconds")


class Score(BaseModel):
    """
    Continuous Calibrated Score Primitive.
    Places unstructured state on a continuous [0.0, 1.0] scale (e.g. relevance, data density).
    """
    score: float = Field(description="Calibrated continuous rating in [0.0, 1.0]")
    confidence: float = Field(default=0.95, description="Certainty of rating")
    latency_ms: float = Field(default=0.0, description="Inference latency in milliseconds")
