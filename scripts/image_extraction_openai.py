import base64
import fitz  # PyMuPDF
import json
import os
from io import BytesIO
from PIL import Image

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Image as RLImage, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


load_dotenv()
client = OpenAI()

def extract_images_from_pdf(pdf_path):
    """
    Extract all images from a PDF file
    Returns a list of image data (as bytes)
    """
    doc = fitz.open(pdf_path)
    images = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Get list of images on this page
        image_list = page.get_images(full=True)
        
        print(f"Page {page_num + 1}: Found {len(image_list)} images")
        
        for img_index, img in enumerate(image_list):
            # Get image data
            xref = img[0]  # Image reference number
            pix = fitz.Pixmap(doc, xref)
            
            # Convert to PIL Image if needed
            if pix.n - pix.alpha < 4:  # GRAY or RGB
                img_data = pix.tobytes("png")
                images.append({
                    'page': page_num + 1,
                    'image_index': img_index,
                    'image_data': img_data,
                    'width': pix.width,
                    'height': pix.height
                })
            else:  # CMYK: convert to RGB first
                pix1 = fitz.Pixmap(fitz.csRGB, pix)
                img_data = pix1.tobytes("png")
                images.append({
                    'page': page_num + 1,
                    'image_index': img_index,
                    'image_data': img_data,
                    'width': pix1.width,
                    'height': pix1.height
                })
                pix1 = None
            
            pix = None
    
    doc.close()
    return images

def image_bytes_to_base64(image_bytes):
    """
    Convert image bytes to base64 string
    """
    return base64.b64encode(image_bytes).decode('utf-8')

def process_image_with_openai(base64_image, prompt="Analyze this image"):
    """
    Send image to OpenAI Vision API
    """
#     prompt = f"""
# You are analyzing a structured assessment report image. Check if the image contains all of the following elements:

#     A bell curve diagram with category labels:
#         “Much less than others”, “Less than others”, “Just like the majority of others”, “More than others”, “Much more than others”
#         Two green section headers:
#             “Sensory Section”
#             “Behavioral Section”
#         These processing labels:
#             “GENERAL Processing”
#             “AUDITORY Processing”
#             “VISUAL Processing”
#             “TOUCH Processing”
#             “MOVEMENT Processing”
#             “ORAL SENSORY Processing”
#             “BEHAVIORAL responses associated with sensory processing”
#     Score ranges with dashes (e.g., “0———2”, “11———22”)
#     One or more diamond symbols (◆)
#     Descriptive text on the far right (e.g., “Sabrina responds more to sounds than others”)

# ✅ If all of the above elements are clearly visible in the image, respond only with the following JSON:
# RESPONSE FORMAT:
# {{
#     "found": "REPLACE THE CONTENT WITH True IF IMAGE IS FOUND ELSE False"
# }}
#     """


    prompt = """
    You are analyzing an assessment scoring table image. Check if the image includes all of the following elements:

        A bell curve diagram with five labeled scoring categories:
            “Much less than others”
            “Less than others”
            “Just like the majority of others”
            “More than others”
            “Much more than others”
            A blue section header labeled “Quadrant”
        The following four quadrant labels:
            “Seeking/Seeker”
            “Avoiding/Avoider”
            “Sensitivity/Sensor”
            “Registration/Bystander”
        Score ranges with dashes, such as:
            “0———17”
            “18———22”
            “23———33”
            “34———35”
            “27———55”
            “35———65”
    At least one diamond symbol (◆) used to indicate scoring
    Descriptive summary text at the far right of each row (e.g., “Sabrina is just as interested in sensory experiences as the majority of others”)

    RESPONSE FORMAT:
    {{
        "found": "REPLACE THE CONTENT WITH True IF IMAGE IS FOUND ELSE False"
    }}

    """
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-2024-04-09",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=1000,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error with OpenAI Vision API: {e}")
        return None
    

def clip_image_section(img_info, left, top, right, bottom):
    """
    Clip a section from the image using pixel coordinates
    Args:
        img_info: The image info dict from extract_images_from_pdf
        left, top, right, bottom: Pixel coordinates for the crop box
    Returns:
        Cropped image as bytes
    """
    # Convert bytes to PIL Image
    image = Image.open(BytesIO(img_info['image_data']))
    
    # Crop the image (left, top, right, bottom)
    cropped = image.crop((left, top, right, bottom))
    
    # Convert back to bytes
    img_bytes = BytesIO()
    cropped.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes.getvalue()


# Main execution
if __name__ == "__main__":
    pdf_path = "assets/inputs/Sensory-image-Profile-2-Summary-Report_70247631_1751134355067.pdf"
    
    # Extract all images from PDF
    extracted_images = extract_images_from_pdf(pdf_path)
    
    print(f"Total images extracted: {len(extracted_images)}")

    doc = SimpleDocTemplate("output_pdf_path.pdf", pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Process each extracted image
    for i, img_info in enumerate(extracted_images):
        print(f"\n--- Processing Image {i+1} (Page {img_info['page']}) ---")
        print(f"Image size: {img_info['width']}x{img_info['height']}")
        
        # Convert to base64
        base64_image = image_bytes_to_base64(img_info['image_data'])
        
        # Optional: Save image to file for inspection
        # with open(f"extracted_image_{i+1}_page_{img_info['page']}.png", "wb") as f:
        #     f.write(img_info['image_data'])
        
        # Send to OpenAI
        prompt = "Extract any table data, text, or describe the content of this image."
        result = process_image_with_openai(base64_image, prompt)
        result = result.replace("```json", "").replace("```", "")
        
        try:
            result_json = json.loads(result)
            print(result_json)
        except json.JSONDecodeError as e:
            continue


        if (
            (type(result_json['found']) == bool and result_json['found'] == False) or 
            (type(result_json['found']) == str and result_json['found'].lower() == "false")
        ):
            continue
        # top = int(result_json['top'])
        # right = int(result_json['right'])
        # bottom = int(result_json['bottom'])
        # left = int(result_json['left'])

        
        
        # page_image = Image.open(BytesIO(img_info['image_data']))
        # width, height = page_image.size

        # croped = page_image.crop((left, top, right, bottom))
        # temp_buffer = BytesIO()
        # croped.save(temp_buffer, format='PNG')
        # temp_buffer.seek(0)

        with open(f"crop_image_{i}.png", "wb+") as f:
            f.write(img_info['image_data'])

        # Add cropped image to PDF
        # Calculate size to fit on page
        # max_width = 6 * inch
        # max_height = 4 * inch
        
        # img_width, img_height = croped.size
        # scale = min(max_width / img_width, max_height / img_height)
        
        # rl_image = RLImage(temp_buffer, width=img_width * scale, height=img_height * scale)
        # story.append(rl_image)
        # story.append(Spacer(1, 12))

        if result:
            print(f"OpenAI Response for Image {i+1}:")
            print(result)
            print("-" * 50)
            

    # Build PDF
    doc.build(story)
    print(f"PDF saved as: output_pdf_path.pdf")
