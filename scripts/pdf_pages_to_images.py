import os
import sys
from pathlib import Path

from pdf2image import convert_from_path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

sys.path.append(str(PROJECT_DIR))


# Path to your input PDF
input_pdf_path = '/home/lap-49/Downloads/Bayley-4-Cognitive-Language-and-Motor-Scales-Score-Report_70360701_1751082282441.pdf'

# Output directory for separate PDFs
output_path = os.path.join(PROJECT_DIR, 'assets', 'inputs', "Bayley-image-4-Cognitive-Language-and-Motor-Scales-Score-Report_70360701_1751082282441.pdf")

# Convert PDF pages to images
print("Converting PDF pages to images...")
images = convert_from_path(input_pdf_path)

# Save each image as a separate PDF
pages = []
for i, image in enumerate(images):
    image_rgb = image.convert('RGB')  # Ensure RGB format
    pages.append(image_rgb)

pages[0].save(output_path, 'PDF', save_all=True, append_images=pages[1:])
print(f'Saved {output_path}')

print(f'\nDone! {len(images)} pages converted and saved in: {output_path}')
