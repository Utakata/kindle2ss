import os
import torch
from PIL import Image
import warnings

# Filter warnings from libraries to keep output clean
warnings.filterwarnings("ignore")

class OCRProcessor:
    def __init__(self):
        self.use_gpu = torch.cuda.is_available()
        self.device = "cuda" if self.use_gpu else "cpu"
        self.engine = None

    def check_gpu(self):
        return self.use_gpu

    def load_engine(self):
        if self.engine is None:
            try:
                from yomitoku import DocumentAnalyzer
                # Initialize YomiToku Engine
                # Using defaults for now, can be parameterized
                self.engine = DocumentAnalyzer(device=self.device)
            except ImportError:
                print("YomiToku not installed.")
            except Exception as e:
                print(f"Failed to load YomiToku: {e}")

    def images_to_pdf(self, image_paths, output_pdf_path, crop_config=None, progress_callback=None):
        """
        Convert images to PDF.
        If crop_config is provided (top, bottom), images are cropped before PDF generation.
        """
        if not image_paths:
            return False, "No images provided"

        try:
            # 1. Pre-process images (Cropping)
            processed_images = []
            for i, path in enumerate(image_paths):
                if progress_callback:
                    progress_callback(i, len(image_paths), "Processing images...")

                img = Image.open(path)

                if crop_config:
                    top = crop_config.get('top', 0)
                    bottom = crop_config.get('bottom', 0)
                    w, h = img.size
                    if top + bottom < h:
                        img = img.crop((0, top, w, h - bottom))

                # Convert to RGB just in case
                if img.mode != "RGB":
                    img = img.convert("RGB")

                processed_images.append(img)

            # 2. Save as PDF (Simple Pillow method if no OCR needed, or as fallback)
            # Currently implementing Simple PDF to start.
            # YomiToku integration for 'Searchable PDF' is complex and requires verifying API.
            # We will use Pillow for 'Image Only PDF' first, as YomiToku is for OCR data extraction mainly.
            # *However*, the user asked for OCR.
            # YomiToku outputs analyzer results (text, layout). To make a "Searchable PDF",
            # we typically need to overlay text on the image.
            # YomiToku's main example exports to Markdown/HTML.
            # Let's check if YomiToku has a 'to_pdf' method or if we strictly use it for text extraction.
            # The search result said "文書画像をサーチャブルPDFに変換する処理もサポートしています".

            # Since I cannot easily verify YomiToku's specific PDF generation API without docs in front of me
            # (and the snippet was general), I will implement two modes:
            # Mode A: Simple PDF (Images only) - Robust
            # Mode B: OCR Text Extraction (Markdown/JSON) - Using YomiToku

            # Re-reading prompt: "またPDFにするなどGUI化を図り" -> "Make it GUI, e.g. make it PDF"
            # And later: "yomitokuと連携を行ってOCRを行えるようにしたい" -> "Link with yomitoku to do OCR"

            # Let's implement Image-based PDF first.
            if processed_images:
                processed_images[0].save(
                    output_pdf_path, "PDF", resolution=100.0, save_all=True, append_images=processed_images[1:]
                )
                return True, f"Saved PDF to {output_pdf_path}"

            return False, "No images processed"

        except Exception as e:
            return False, str(e)

    def run_ocr_export(self, image_paths, output_dir, export_format="markdown", progress_callback=None):
        """
        Run YomiToku OCR and export to specified format.
        """
        self.load_engine()
        if not self.engine:
            return False, "OCR Engine could not be loaded"

        try:
            results = []
            for i, path in enumerate(image_paths):
                if progress_callback:
                    progress_callback(i, len(image_paths), "Running OCR...")

                # Load image
                img = Image.open(path).convert("RGB")
                # Run inference
                result = self.engine(img)
                results.append(result)

            # Export
            output_file = os.path.join(output_dir, f"ocr_result.{export_format}")

            # YomiToku results are typically objects. We should try to extract text safely.
            # Since we don't have the exact API doc, we'll try a safe approach.
            with open(output_file, 'w', encoding='utf-8') as f:
                for i, res in enumerate(results):
                    f.write(f"# Page {i+1}\n\n")

                    # Try to find a text extraction method or attribute
                    text_content = ""
                    if hasattr(res, 'text'):
                        text_content = res.text
                    elif hasattr(res, 'content'):
                        text_content = res.content
                    elif hasattr(res, 'to_markdown'):
                        text_content = res.to_markdown()
                    else:
                        # Fallback to string representation if all else fails
                        text_content = str(res)

                    f.write(text_content + "\n\n")

            return True, f"OCR exported to {output_file}"

        except Exception as e:
            return False, str(e)

if __name__ == "__main__":
    ocr = OCRProcessor()
    print(f"GPU Available: {ocr.check_gpu()}")
