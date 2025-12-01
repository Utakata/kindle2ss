import unittest
import os
import shutil
from PIL import Image
from src.core.capture_engine import CaptureEngine
from src.core.ocr_processor import OCRProcessor

class TestCaptureEngine(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_output_engine"
        os.makedirs(self.test_dir, exist_ok=True)
        self.engine = CaptureEngine(save_dir=self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_init(self):
        self.assertEqual(self.engine.save_dir, self.test_dir)
        self.assertEqual(self.engine.interval, 1.0)

    def test_duplicate_logic(self):
        # Create two identical images
        img1 = Image.new('RGB', (100, 100), color = 'red')
        img2 = Image.new('RGB', (100, 100), color = 'red')

        self.engine.set_crop_margins(0, 0)
        self.assertTrue(self.engine._is_duplicate(img1, img2))

        # Create different image
        img3 = Image.new('RGB', (100, 100), color = 'blue')
        self.assertFalse(self.engine._is_duplicate(img1, img3))

    def test_duplicate_with_crop(self):
        # Image with changing header but same body
        img1 = Image.new('RGB', (100, 100), color = 'white')
        # Draw header on img1
        for x in range(100):
            img1.putpixel((x, 5), (0, 0, 0)) # Line at y=5

        img2 = Image.new('RGB', (100, 100), color = 'white')
        # Draw different header on img2
        for x in range(100):
            img2.putpixel((x, 5), (255, 0, 0)) # Red Line at y=5

        # Without crop, they are different
        self.engine.set_crop_margins(0, 0)
        self.assertFalse(self.engine._is_duplicate(img1, img2))

        # With crop (top 10px), they should be identical (both white body)
        self.engine.set_crop_margins(10, 0)
        self.assertTrue(self.engine._is_duplicate(img1, img2))

class TestOCRProcessor(unittest.TestCase):
    def setUp(self):
        self.ocr = OCRProcessor()
        self.test_dir = "test_output_ocr"
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_images_to_pdf_creation(self):
        # Create dummy images
        img1 = Image.new('RGB', (100, 100), color='white')
        p1 = os.path.join(self.test_dir, "1.png")
        img1.save(p1)

        img2 = Image.new('RGB', (100, 100), color='black')
        p2 = os.path.join(self.test_dir, "2.png")
        img2.save(p2)

        pdf_path = os.path.join(self.test_dir, "output.pdf")

        success, msg = self.ocr.images_to_pdf([p1, p2], pdf_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(pdf_path))

if __name__ == '__main__':
    unittest.main()
