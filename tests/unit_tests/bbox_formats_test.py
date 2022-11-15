import unittest

import numpy as np
import torch

from super_gradients.common.factories import BBoxFormatFactory
from super_gradients.training.utils.bbox_formats import (
    CXCYWHCoordinateFormat,
    NormalizedXYXYCoordinateFormat,
    NormalizedXYWHCoordinateFormat,
    XYWHCoordinateFormat,
    YXYXCoordinateFormat,
    XYXYCoordinateFormat,
    NormalizedCXCYWHCoordinateFormat,
    convert_bboxes,
    BBOX_FORMATS,
    BoundingBoxFormat,
)


class BBoxFormatsTest(unittest.TestCase):
    def setUp(self):
        # contains all formats
        self.formats = [
            XYWHCoordinateFormat(),
            XYXYCoordinateFormat(),
            YXYXCoordinateFormat(),
            CXCYWHCoordinateFormat(),
            NormalizedXYWHCoordinateFormat(),
            NormalizedXYXYCoordinateFormat(),
            NormalizedCXCYWHCoordinateFormat(),
        ]

        self.image_shape = (2048, 1536)

        inv_h = 1.0 / self.image_shape[0]
        inv_w = 1.0 / self.image_shape[1]

        # Set of bounding boxes with manually computed coordinates for a regression testing
        self.bounding_bboxes = [
            # 1x1 bounding box
            {
                "xyxy": [1, 2, 2, 3],
                "yxyx": [2, 1, 3, 2],
                "xywh": [1, 2, 1, 1],
                "cxcywh": [1.5, 2.5, 1, 1],
                "normalized_xywh": [1 * inv_w, 2 * inv_h, 1 * inv_w, 1 * inv_h],
                "normalized_xyxy": [1 * inv_w, 2 * inv_h, 2 * inv_w, 3 * inv_h],
                "normalized_cxcywh": [1.5 * inv_w, 2.5 * inv_h, 1 * inv_w, 1 * inv_h],
            },
            # 2x4 bounding box
            {
                "xyxy": [1, 13, 3, 17],
                "yxyx": [13, 1, 17, 3],
                "xywh": [1, 13, 2, 4],
                "cxcywh": [2, 15, 2, 4],
                "normalized_xywh": [1 * inv_w, 13 * inv_h, 2 * inv_w, 4 * inv_h],
                "normalized_xyxy": [1 * inv_w, 13 * inv_h, 3 * inv_w, 17 * inv_h],
                "normalized_cxcywh": [2 * inv_w, 15 * inv_h, 2 * inv_w, 4 * inv_h],
            },
            # bounding box covering entire image shape
            {
                "xyxy": [0, 0, self.image_shape[1], self.image_shape[0]],
                "yxyx": [0, 0, self.image_shape[0], self.image_shape[1]],
                "xywh": [0, 0, self.image_shape[1], self.image_shape[0]],
                "cxcywh": [self.image_shape[1] * 0.5, self.image_shape[0] * 0.5, self.image_shape[1], self.image_shape[0]],
                "normalized_xywh": [0, 0, 1, 1],
                "normalized_xyxy": [0, 0, 1, 1],
                "normalized_cxcywh": [0.5, 0.5, 1, 1],
            },
        ]

    def test_conversion_to_from_is_correct_2d_input_tensor(self):
        """
        Check whether bbox format supports 3D input shape as input: [L, 4]
        """
        gt_bboxes = torch.randint(low=0, high=512, size=(8192, 4)).float()
        # Make bboxes in XYXY format and ensure they all of non-zero area with X2>X1 and Y2>Y1
        gt_bboxes[..., 2:4] += gt_bboxes[..., 0:2] + 1

        image_shape = self.image_shape

        for fm1 in self.formats:
            input_bboxes = gt_bboxes.clone()
            intermediate_format = fm1.from_xyxy(input_bboxes, image_shape, inplace=False)
            actual_bboxes = fm1.to_xyxy(intermediate_format, image_shape, inplace=False)
            self.assertTrue(torch.allclose(input_bboxes, actual_bboxes, atol=1, rtol=1), msg=f"Format {fm1} failed to pass sanity check")

            input_bboxes = gt_bboxes.clone()
            intermediate_format = fm1.from_xyxy(input_bboxes, image_shape, inplace=True)
            # Since we pass inplace=True the input bboxes must be modified inplace
            self.assertTrue(torch.allclose(input_bboxes, intermediate_format, atol=1e-8, rtol=1e-8), msg=f"Format {fm1} failed to pass sanity check")

            actual_bboxes = fm1.to_xyxy(intermediate_format, image_shape, inplace=True)
            # Since we pass inplace=True the input bboxes must be modified inplace
            self.assertTrue(torch.allclose(input_bboxes, actual_bboxes, atol=1e-8, rtol=1e-8), msg=f"Format {fm1} failed to pass sanity check")

            self.assertTrue(torch.allclose(gt_bboxes, actual_bboxes, atol=1, rtol=1), msg=f"Format {fm1} failed to pass sanity check")

    def test_conversion_to_from_is_correct_2d_input_numpy_array(self):
        """
        Check whether bbox format supports 3D input shape as input: [L, 4]
        """
        gt_bboxes = np.random.randint(low=0, high=512, size=(8192, 4)).astype(np.float32)
        # Make bboxes in XYXY format and ensure they all of non-zero area with X2>X1 and Y2>Y1
        gt_bboxes[..., 2:4] += gt_bboxes[..., 0:2] + 1

        image_shape = self.image_shape

        for fm1 in self.formats:
            input_bboxes = gt_bboxes.copy()
            intermediate_format = fm1.from_xyxy(input_bboxes, image_shape, inplace=False)
            actual_bboxes = fm1.to_xyxy(intermediate_format, image_shape, inplace=False)
            self.assertTrue(np.allclose(input_bboxes, actual_bboxes, atol=1, rtol=1), msg=f"Format {fm1} failed to pass sanity check")

            input_bboxes = gt_bboxes.copy()
            intermediate_format = fm1.from_xyxy(input_bboxes, image_shape, inplace=True)
            # Since we pass inplace=True the input bboxes must be modified inplace
            self.assertTrue(np.allclose(input_bboxes, intermediate_format, atol=1e-8, rtol=1e-8), msg=f"Format {fm1} failed to pass sanity check")

            actual_bboxes = fm1.to_xyxy(intermediate_format, image_shape, inplace=True)
            # Since we pass inplace=True the input bboxes must be modified inplace
            self.assertTrue(np.allclose(input_bboxes, actual_bboxes, atol=1e-8, rtol=1e-8), msg=f"Format {fm1} failed to pass sanity check")

            self.assertTrue(np.allclose(gt_bboxes, actual_bboxes, atol=1, rtol=1), msg=f"Format {fm1} failed to pass sanity check")

    def test_conversion_to_from_is_correct_3d_input(self):
        """
        Check whether bbox format supports 3D input shape as input: [B, L, 4]
        """
        gt_bboxes = torch.randint(low=0, high=512, size=(16, 8192, 4)).float()
        # Make bboxes in XYXY format and ensure they all of non-zero area with X2>X1 and Y2>Y1
        gt_bboxes[..., 2:4] += gt_bboxes[..., 0:2] + 1

        image_shape = self.image_shape

        for fm1 in self.formats:
            input_bboxes = gt_bboxes.clone()
            intermediate_format = fm1.from_xyxy(input_bboxes, image_shape, inplace=False)
            actual_bboxes = fm1.to_xyxy(intermediate_format, image_shape, inplace=False)
            self.assertTrue(torch.allclose(input_bboxes, actual_bboxes, atol=1, rtol=1), msg=f"Format {fm1} failed to pass sanity check")

    def test_convert_bboxes(self):
        gt_bboxes = torch.randint(low=0, high=512, size=(16, 8192, 4)).float()
        # Make bboxes in XYXY format and ensure they all of non-zero area with X2>X1 and Y2>Y1
        gt_bboxes[..., 2:4] += gt_bboxes[..., 0:2] + 1

        image_shape = self.image_shape

        for src_fmt in self.formats:
            for dst_fmt in self.formats:
                input_bboxes = src_fmt.from_xyxy(gt_bboxes, image_shape, inplace=False)
                intermediate_format = convert_bboxes(input_bboxes, image_shape, src_fmt, dst_fmt, inplace=False)
                actual_bboxes = dst_fmt.to_xyxy(intermediate_format, image_shape, inplace=False)
                self.assertTrue(
                    torch.allclose(gt_bboxes, actual_bboxes, atol=1, rtol=1), msg=f"convert_bboxes failed to convert bboxes from {src_fmt} to {dst_fmt}"
                )

    def test_bbox_conversion_regression(self):
        # Convert bounding boxes to a dictionary of bboxes
        bounding_bboxes = {k: np.array([dic[k] for dic in self.bounding_bboxes]) for k in self.bounding_bboxes[0]}
        gt_bboxes = bounding_bboxes["xyxy"]

        image_shape = self.image_shape

        for src_fmt in self.formats:
            input_bboxes = src_fmt.from_xyxy(gt_bboxes, image_shape, inplace=False)
            if src_fmt.format in bounding_bboxes:
                np.testing.assert_allclose(input_bboxes, bounding_bboxes[src_fmt.format], rtol=1e-4, atol=1e-4)

            for dst_fmt in self.formats:
                intermediate_format = convert_bboxes(input_bboxes, image_shape, src_fmt, dst_fmt, inplace=False)
                actual_bboxes = dst_fmt.to_xyxy(intermediate_format, image_shape, inplace=False)
                np.testing.assert_allclose(actual_bboxes, gt_bboxes, rtol=1e-4, atol=1e-4)

    def test_bbox_formats_factory_test(self):
        factory = BBoxFormatFactory()

        for format_key in BBOX_FORMATS.keys():
            format: BoundingBoxFormat = factory.get(format_key)
            self.assertEqual(format_key, format.format)


if __name__ == "__main__":
    unittest.main()