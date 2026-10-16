"""
Unit tests for OpticalDiffer and SeatSaliencyDetector.
"""

import unittest
import numpy as np
from milli_scrapes.optical.differ import OpticalDiffer
from milli_scrapes.optical.saliency import SeatSaliencyDetector


class TestOpticalDiffer(unittest.TestCase):

    def test_optical_differ_identical_frames(self):
        frame_a = np.ones((100, 100, 3), dtype=np.uint8) * 128
        frame_b = np.ones((100, 100, 3), dtype=np.uint8) * 128

        differ = OpticalDiffer()
        res = differ.compute_diff(frame_a, frame_b)

        self.assertFalse(res["has_changed"])
        self.assertEqual(res["change_percent"], 0.0)
        self.assertIsNone(res["bounding_box"])

    def test_optical_differ_changed_frames(self):
        frame_a = np.zeros((100, 100, 3), dtype=np.uint8)
        frame_b = np.zeros((100, 100, 3), dtype=np.uint8)
        # Change a 30x30 block
        frame_b[10:40, 20:50, :] = 255

        differ = OpticalDiffer(change_percent_trigger=0.1)
        res = differ.compute_diff(frame_a, frame_b)

        self.assertTrue(res["has_changed"])
        self.assertGreater(res["change_percent"], 5.0)
        self.assertIsNotNone(res["bounding_box"])
        self.assertEqual(res["bounding_box"], (20, 10, 30, 30))

        # Verify in-memory JPEG rendering
        jpeg_bytes = differ.render_visual_proof_jpeg(frame_b, diff_mask=res["diff_mask"])
        self.assertTrue(len(jpeg_bytes) > 100)
        self.assertEqual(jpeg_bytes[:2], b"\xff\xd8")  # JPEG magic bytes

    def test_seat_saliency_detector(self):
        # Create a frame with red background (all booked) and 1 green available seat
        frame = np.ones((200, 200, 3), dtype=np.uint8) * 50
        # Seat 1: green target (46, 204, 113)
        frame[50:70, 80:100, 0] = 46
        frame[50:70, 80:100, 1] = 204
        frame[50:70, 80:100, 2] = 113

        detector = SeatSaliencyDetector()
        seats = detector.find_available_seats(frame)

        self.assertEqual(len(seats), 1)
        self.assertTrue(75 <= seats[0]["screen_x"] <= 105)
        self.assertTrue(45 <= seats[0]["screen_y"] <= 75)
        self.assertGreaterEqual(seats[0]["confidence"], 0.9)


if __name__ == "__main__":
    unittest.main()
