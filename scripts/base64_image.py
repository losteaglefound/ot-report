from PIL import Image
from io import BytesIO
import base64

file = "/home/lap-49/Documents/ot-report/scripts/outputs/ocr_results/texts/page_3_img_0.txt"
img_b64_str: str | None = None
with open(file, 'r') as f:
    lines = f.readlines()
    img_b64_str = lines[0].strip()

# Validate image can be decoded
img_data = base64.b64decode(img_b64_str)
image = Image.open(BytesIO(img_data))
image.show()  # Opens the image for visual confirmation
