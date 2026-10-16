"""
Milli-Scrapes Optical Subsystem.
Operates directly on transient RAM frame buffers with zero disk I/O.
Provides microsecond visual diffing and interactive canvas seat saliency detection.
"""

from .differ import OpticalDiffer
from .saliency import SeatSaliencyDetector

__all__ = ["OpticalDiffer", "SeatSaliencyDetector"]
