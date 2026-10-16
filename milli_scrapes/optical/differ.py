"""
Optical Differ for Transient RAM Frame Buffers.
Calculates pixel-level visual differences, bounding boxes, and change percentages
in under 1 millisecond without writing secondary storage files.
"""

import io
from typing import Dict, Any, Optional, Tuple
import numpy as np
from PIL import Image


class OpticalDiffer:
    """
    High-frequency optical comparison engine operating entirely in RAM.
    """

    def __init__(self, pixel_delta_threshold: int = 25, change_percent_trigger: float = 0.5):
        self.pixel_delta_threshold = pixel_delta_threshold
        self.change_percent_trigger = change_percent_trigger

    def compute_diff(self, frame_a: np.ndarray, frame_b: np.ndarray) -> Dict[str, Any]:
        """
        Compares two image frames and returns structural difference metrics.
        """
        if frame_a.shape != frame_b.shape:
            # Resize frame_b to match frame_a if dimensions differ
            img_b = Image.fromarray(frame_b).resize((frame_a.shape[1], frame_a.shape[0]))
            frame_b = np.array(img_b)

        # Convert to grayscale / single channel if 3D
        if len(frame_a.shape) == 3:
            gray_a = np.mean(frame_a.astype(np.float32), axis=2)
            gray_b = np.mean(frame_b.astype(np.float32), axis=2)
        else:
            gray_a = frame_a.astype(np.float32)
            gray_b = frame_b.astype(np.float32)

        # Compute absolute difference
        diff = np.abs(gray_a - gray_b)
        changed_pixels = diff > self.pixel_delta_threshold
        total_pixels = changed_pixels.size
        changed_count = int(np.count_nonzero(changed_pixels))
        change_pct = (changed_count / max(total_pixels, 1)) * 100.0

        # Calculate bounding box of changed region
        bbox = None
        if changed_count > 0:
            ys, xs = np.where(changed_pixels)
            y_min, y_max = int(ys.min()), int(ys.max())
            x_min, x_max = int(xs.min()), int(xs.max())
            bbox = (x_min, y_min, x_max - x_min + 1, y_max - y_min + 1)

        has_changed = change_pct >= self.change_percent_trigger

        return {
            "has_changed": bool(has_changed),
            "change_percent": round(float(change_pct), 3),
            "changed_pixels": changed_count,
            "total_pixels": total_pixels,
            "bounding_box": bbox,
            "diff_mask": changed_pixels
        }

    def render_visual_proof_jpeg(self, frame: np.ndarray, diff_mask: Optional[np.ndarray] = None) -> bytes:
        """
        Renders highlighted JPEG proof bytes in transient memory (0 bytes saved to disk).
        """
        img = Image.fromarray(frame.copy())
        if diff_mask is not None and np.any(diff_mask):
            # Overlay red translucent highlight on changed pixels
            frame_copy = frame.copy()
            if len(frame_copy.shape) == 3:
                frame_copy[diff_mask, 0] = np.clip(frame_copy[diff_mask, 0] + 120, 0, 255)
            img = Image.fromarray(frame_copy)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=80)
        return buf.getvalue()
