"""
Seat & Slot Visual Saliency Detector.
Finds candidate available seats and booking slots on interactive Canvas/SVG layouts.
Resolves centroid coordinates in sub-millisecond execution.
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np


class SeatSaliencyDetector:
    """
    Detects optical color centroids corresponding to available seats or slots.
    """

    # Default color for 'Available' seats is green (RGB ~ [46, 204, 113] or [0, 255, 0])
    DEFAULT_AVAILABLE_RGB = (46, 204, 113)

    def __init__(self, target_rgb: Tuple[int, int, int] = DEFAULT_AVAILABLE_RGB, tolerance: int = 40):
        self.target_rgb = target_rgb
        self.tolerance = tolerance

    def find_available_seats(self, frame: np.ndarray, min_cluster_size: int = 15) -> List[Dict[str, Any]]:
        """
        Scans frame buffer in RAM for clusters matching target color.
        Returns list of seat centroids sorted by position.
        """
        if len(frame.shape) != 3:
            return []

        r, g, b = self.target_rgb
        tol = self.tolerance

        # Distance mask in RGB space
        r_diff = np.abs(frame[:, :, 0].astype(int) - r)
        g_diff = np.abs(frame[:, :, 1].astype(int) - g)
        b_diff = np.abs(frame[:, :, 2].astype(int) - b)

        match_mask = (r_diff <= tol) & (g_diff <= tol) & (b_diff <= tol)

        if not np.any(match_mask):
            return []

        ys, xs = np.where(match_mask)
        if len(xs) < min_cluster_size:
            return []

        from scipy.ndimage import label, center_of_mass

        labeled_array, num_features = label(match_mask)
        if num_features == 0:
            return []

        seats = []
        for feat_id in range(1, num_features + 1):
            feat_pixels = np.count_nonzero(labeled_array == feat_id)
            if feat_pixels >= min_cluster_size:
                cy, cx = center_of_mass(match_mask, labeled_array, feat_id)
                seats.append({
                    "screen_x": int(round(cx)),
                    "screen_y": int(round(cy)),
                    "pixel_count": int(feat_pixels),
                    "confidence": round(min(1.0, feat_pixels / 50.0), 2)
                })

        return sorted(seats, key=lambda s: (s["screen_y"], s["screen_x"]))
