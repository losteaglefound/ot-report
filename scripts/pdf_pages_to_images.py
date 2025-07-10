import os
import sys
from pathlib import Path

from pdf2image import convert_from_path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

sys.path.append(str(PROJECT_DIR))


def convert_to_image_pdf():
    # Path to your input PDF
    input_pdf_path = 'assets/inputs/PediEAT_Full_Version_2024-2-12.pdf'

    # Output directory for separate PDFs
    output_path = os.path.join(PROJECT_DIR, 'assets', 'inputs', "PediEAT-image_Full_Version_2024-2-12.pdf")

    # Convert PDF pages to images
    print("Converting PDF pages to images...")
    images = convert_from_path(input_pdf_path)

    # Save each image as a separate PDF
    pages = []
    for i, image in enumerate(images):
        print(i)
        image_rgb = image.convert('RGB')  # Ensure RGB format
        pages.append(image_rgb)

    pages[0].save(output_path, 'PDF', save_all=True, append_images=pages[1:])
    print(f'Saved {output_path}')

    print(f'\nDone! {len(images)} pages converted and saved in: {output_path}')
    return output_path


if __name__ == "__main__":
    convert_to_image_pdf()