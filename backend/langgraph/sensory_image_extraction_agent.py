import base64
import io
import json
import os
from pathlib import Path
import sys
from typing import Any, Literal, TypedDict

import fitz
from langgraph.graph import (
    END,
    StateGraph, 
    START
)
from openai import OpenAI
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Image, Spacer, PageBreak
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.platypus.flowables import Flowable

from config import config as server_config

quandrant_prompt = """
    You are analyzing an assessment scoring table image. Check if the image includes all of the following elements:

        A bell curve diagram with five labeled scoring categories:
            "Much less than others"
            "Less than others"
            "Just like the majority of others"
            "More than others"
            "Much more than others"
            A blue section header labeled "Quadrant"
        The following four quadrant labels:
            "Seeking/Seeker"
            "Avoiding/Avoider"
            "Sensitivity/Sensor"
            "Registration/Bystander"
        Score ranges with dashes, such as:
            "0———17"
            "18———22"
            "23———33"
            "34———35"
            "27———55"
            "35———65"
    At least one diamond symbol (◆) used to indicate scoring
    Descriptive summary text at the far right of each row (e.g., "Sabrina is just as interested in sensory experiences as the majority of others")

    RESPONSE FORMAT:
    {{
        "found": "REPLACE THE CONTENT WITH True IF IMAGE IS FOUND ELSE False"
    }}



IMPORTANT:
- Return True / False in string form like 'True' / 'False'.

"""

social_and_behavioural_prompt = f"""
You are analyzing a structured assessment report image. Check if the image contains all of the following elements:

    A bell curve diagram with category labels:
        "Much less than others", "Less than others", "Just like the majority of others", "More than others", "Much more than others"
        Two green section headers:
            "Sensory Section"
            "Behavioral Section"
        These processing labels:
            "GENERAL Processing"
            "AUDITORY Processing"
            "VISUAL Processing"
            "TOUCH Processing"
            "MOVEMENT Processing"
            "ORAL SENSORY Processing"
            "BEHAVIORAL responses associated with sensory processing"
    Score ranges with dashes (e.g., "0———2", "11———22")
    One or more diamond symbols (◆)
    Descriptive text on the far right (e.g., "Sabrina responds more to sounds than others")

✅ If all of the above elements are clearly visible in the image, respond only with the following JSON:
RESPONSE FORMAT:
{{
    "found": "REPLACE THE CONTENT WITH 'True' IF IMAGE IS FOUND ELSE 'False'"
}}

IMPORTANT:
- Return True / False in string form like 'True' / 'False'.
    """


class State(TypedDict):
    prompts: dict[Literal['quadrant', 'social_and_behavioural'], str]
    openai_client: Any
    base64_image: str | None
    pdf_path: str | None
    pages: list
    found_pages: list
    error: str | None
    out_path: str


def extract_images_from_pdf(state: dict):
    """
    Extract all images from a PDF file
    Returns a list of image data (as bytes)
    """

    pdf_path = state['pdf_path']

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

    return {"pages": images}


def find_quadrant_image(state: State):
    """
    Send image to OpenAI Vision API
    """
    print("Starting searching for quandrant score table")
    client = state['openai_client']
    prompt = state['prompts']['quadrant']
    pages = state['pages']

    try:
        for i, page in enumerate(pages):
            base64_image = image_bytes_to_base64(page['image_data'])

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
            result =  response.choices[0].message.content
            
            result = result.replace("```json", "").replace("```", "")
            
            result_json: dict | None = None
            try:
                result_json = json.loads(result)
                print(result_json)
            except json.JSONDecodeError as e:
                print("json decode error")
                print("error result:", result)

            if result_json:
                if (
                    (type(result_json['found']) == bool and result_json['found'] == False) or 
                    (type(result_json['found']) == str and result_json['found'].lower() == "false")
                ):
                    continue

            state['found_pages'].append(i)
            break

        return state

    except Exception as e:
        print(f"Error with OpenAI Vision API: {e}")
        state['error'] = f"Error enountered while processing {str(e)}"
        return state


def find_social_and_behavioural_image(state: State):
    """
    Send image to OpenAI Vision API
    """
    print("Starting searching for social and score table")
    client = state['openai_client']
    prompt = state['prompts']['social_and_behavioural']
    pages = state['pages']

    try:
        for i, page in enumerate(pages):
            base64_image = image_bytes_to_base64(page['image_data'])

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
            result =  response.choices[0].message.content
            
            result = result.replace("```json", "").replace("```", "")
            
            result_json: dict | None = None
            try:
                result_json = json.loads(result)
                print(result_json)
            except json.JSONDecodeError as e:
                print("json decode error")
                print(result)

            if result_json:
                if (
                    (type(result_json['found']) == bool and result_json['found'] == False) or 
                    (type(result_json['found']) == str and result_json['found'].lower() == "false")
                ):
                    continue
            
            # Add to existing found_pages
            existing_found_pages = state.get('found_pages', [])
            existing_found_pages.append(i)
            return {"found_pages": existing_found_pages}

        return {}

    except Exception as e:
        print(f"Error with OpenAI Vision API: {e}")
        return {"error": f"Error encountered while processing {str(e)}"}


def image_bytes_to_base64(image_bytes):
    """
    Convert image bytes to base64 string
    """
    return base64.b64encode(image_bytes).decode('utf-8')


def create_pdf_with_found_pages(found_pages, pages_data, output_path="output_report.pdf"):
    """
    Create a PDF using ReportLab Platypus with the found pages as full-page images
    
    Args:
        found_pages: List of page indices (from State.found_pages)
        pages_data: List of page data dictionaries (from State.pages)
        output_path: Output PDF file path
    """
    
    # Create document with margins
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=0.5*inch,
        rightMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    # Calculate available space within margins
    page_width = A4[0] - (doc.leftMargin + doc.rightMargin)
    page_height = A4[1] - (doc.topMargin + doc.bottomMargin)
    
    # Story list to hold all flowables
    story = []
    
    for page_index in found_pages:
        # Get the page data
        page_data = pages_data[page_index]
        image_bytes = page_data['image_data']
        original_width = page_data['width']
        original_height = page_data['height']
        
        # Convert bytes to ImageReader
        image_stream = io.BytesIO(image_bytes)
        
        # Calculate scaling to fit within margins while maintaining aspect ratio
        scale_width = page_width / original_width
        scale_height = page_height / original_height
        scale = min(scale_width, scale_height)
        
        # Calculate new dimensions
        new_width = original_width * scale
        new_height = original_height * scale * 0.8
        
        # Create Image flowable - pass the BytesIO stream directly
        image = Image(
            image_stream, # Pass the BytesIO stream directly
            width=new_width,
            height=new_height,
            hAlign='CENTER'
        )
        
        # Add image to story
        story.append(image)
        
        # Add page break if not the last page
        if page_index != found_pages[-1]:
            story.append(PageBreak())
    
    # Build the PDF
    doc.build(story)
    print(f"PDF created successfully: {output_path}")


graph_builder = StateGraph(State)
graph_builder.add_node("extract_pdf_pages", extract_images_from_pdf)
graph_builder.add_node("quadrant_image_search", find_quadrant_image)
graph_builder.add_node("social_and_behavioural_image_search", find_social_and_behavioural_image)

graph_builder.add_edge(START, "extract_pdf_pages")
graph_builder.add_edge('extract_pdf_pages', 'quadrant_image_search')
graph_builder.add_edge('quadrant_image_search', 'social_and_behavioural_image_search')
graph_builder.add_edge("social_and_behavioural_image_search", END)

graph = graph_builder.compile()

def create_elements_from_found_pages(found_pages, pages_data, page_width=None, page_height=None):
    """
    Create ReportLab elements from found pages for integration into existing PDF
    
    Args:
        found_pages: List of page indices (from State.found_pages)
        pages_data: List of page data dictionaries (from State.pages)
        page_width: Available width for images (optional)
        page_height: Available height for images (optional)
    
    Returns:
        List of ReportLab elements (Image, Spacer, etc.)
    """
    
    # Default page dimensions if not provided
    if page_width is None:
        page_width = A4[0] - (2.0*inch)  # More conservative margins
    if page_height is None:
        page_height = A4[1] - (2.0*inch)  # More conservative margins
    
    elements = []
    
    for i, page_index in enumerate(found_pages):
        # Get the page data
        page_data = pages_data[page_index]
        image_bytes = page_data['image_data']
        original_width = page_data['width']
        original_height = page_data['height']
        
        # Convert bytes to BytesIO stream
        image_stream = io.BytesIO(image_bytes)
        
        # Calculate scaling to fit within available space while maintaining aspect ratio
        scale_width = page_width / original_width
        scale_height = page_height / original_height
        scale = min(scale_width, scale_height)
        
        # Calculate new dimensions
        new_width = original_width * scale
        new_height = original_height * scale
        
        # Create Image element
        image = Image(
            image_stream,
            width=new_width,
            height=new_height,
            hAlign='CENTER'
        )
        
        # Add image to elements
        elements.append(image)
        
        # Add spacer if not the last page
        # if i < len(found_pages) - 1:
        #     elements.append(Spacer(1, 20))
    
    return elements


def sensory_image_extract(pdf_path):
    """
    Extract sensory profile images from PDF and return ReportLab elements
    
    Args:
        pdf_path: Path to the PDF file to analyze
        
    Returns:
        List of ReportLab elements ready for integration into PDF
    """
    
    # Create initial state dictionary
    initial_state = State(
        prompts={
            "quadrant": quandrant_prompt,
            "social_and_behavioural": social_and_behavioural_prompt
        },
        openai_client=OpenAI(api_key=server_config.OPENAI_API_KEY),
        base64_image=None,
        pdf_path=pdf_path,
        pages=[],
        found_pages=[],
        error=None,
        out_path='outputs/test_sensory_score_extract.pdf'
    )

    try:
        result = graph.invoke(initial_state)
        
        found_pages = result.get('found_pages', [])
        pages_data = result.get('pages', [])
        
        if found_pages:
            print(f"Found {len(found_pages)} sensory profile images")
            # Return ReportLab elements instead of creating PDF
            return create_elements_from_found_pages(found_pages, pages_data)
        else:
            print("No sensory profile images found")
            return []
            
    except Exception as e:
        print(f"Error extracting sensory profile images: {e}")
        return []
 