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

from sconfig import config as sconfig
from config import config as server_config



# subtest_scaled_and_standard_score_prompt = """
#     You are analyzing a psychological or developmental assessment report image. Return a JSON response based on whether the following elements are clearly present:

#     1. A section header titled: "SCORE SUMMARY"
#     2. A table titled: "Subtest Scaled Score Summary" with these column headers:
#         "Scale Subtest"
#         "Raw score"
#         "Scaled score"
#         "Age equivalent"
#         "Growth scale value"
#     3. Subtest names present under categories:
#         Cognitive: “Cognitive (CG)”
#         Language: “Receptive Communication (RC)”, “Expressive Communication (EC)”
#         Motor: “Fine Motor (FM)”, “Gross Motor (GM)”
#     4. A second table titled: "Standard Score Summary" with these column headers:
#         "Scale Score"
#         "Sum of scaled scores"
#         "Standard score"
#         "Percentile rank"
#         "90% Confidence interval"
#         "Descriptive classification"
#     5. Row labels in the second table:
#         “Cognitive (COG)”
#         “Language (LANG)”
#         “Motor (MOT)”
#     6. The phrase "Extremely low" must appear in the "Descriptive classification" column.

#     RESPONSE FORMAT:
#     {{
#         "found": "REPLACE THE CONTENT WITH 'True' IF IMAGE IS FOUND ELSE 'False'"
#     }}

# """

subtest_scaled_and_standard_score_prompt = f"""
    You are analyzing a psychological or developmental assessment report image. Return a JSON response based on whether the following elements are clearly present:

    1. Main Section Header
        The report must begin with the heading:
            “SCORE SUMMARY” (case-insensitive).

        It must be clearly styled or positioned as a section title (e.g., bold, larger font, top of the page).

    2. First Table – “Subtest Scaled Score Summary”
        A full-width table must appear under the subheading:
            “Subtest Scaled Score Summary”

        The table must have exactly these 5 column headers in this order:
            “Scale Subtest”
            “Raw score”
            “Scaled score”
            “Age equivalent”
            “Growth scale value”

        The table rows must be organized into three labeled categories:
            Cognitive
                Must include: “Cognitive (CG)”
            Language
                Must include: “Receptive Communication (RC)” and “Expressive Communication (EC)”
            Motor
                Must include: “Fine Motor (FM)” and “Gross Motor (GM)”

    3. Second Table – “Standard Score Summary”
        A second table must appear under a clearly separated subheading:
            “Standard Score Summary”

        The table must contain exactly these 6 column headers in this order:
            “Scale Score”
            “Sum of scaled scores”
            “Standard score”
            “Percentile rank”
            “90% Confidence interval”
            “Descriptive classification”
        The left column (“Scale Score”) must include the following three row labels:
            “Cognitive (COG)”
            “Language (LANG)”
            “Motor (MOT)”
        The rightmost column, titled “Descriptive classification”, must contain the phrase:
            “Extremely low” at least once, and ideally in all three rows.

    RESPONSE FORMAT:
    {{
        "found": "REPLACE THE CONTENT WITH 'True' IF IMAGE IS FOUND ELSE 'False'"
    }}

"""


class State(TypedDict):
    prompts: dict[Literal['subtest_scaled_and_standard_score_prompt'], str]
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


def find_subtest_scaled_and_standard_score(state: State):
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
                
            try:
                result_json = json.loads(result)
                print(result_json)
            except json.JSONDecodeError as e:
                print("json decode error")
                print(result)

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
        new_height = original_height * scale
        
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
graph_builder.add_node("search_subtest_scaled_and_standard_score", find_subtest_scaled_and_standard_score)

graph_builder.add_edge(START, "extract_pdf_pages")
graph_builder.add_edge('extract_pdf_pages', 'search_subtest_scaled_and_standard_score')
graph_builder.add_edge('search_subtest_scaled_and_standard_score', END)

graph = graph_builder.compile()

def main():
    
    pdf_path = "assets/inputs/images/Bayley-image-4-Cognitive-Language-and-Motor-Scales-Score-Report_70360701_1751082282441.pdf"
    
    # Create initial state dictionary
    initial_state = State(
        prompts={
            "quadrant": subtest_scaled_and_standard_score_prompt
        },
        openai_client=OpenAI(api_key=server_config.OPENAI_API_KEY),
        base64_image=None,
        pdf_path=pdf_path,
        pages=[],
        found_pages=[],
        error=None,
        out_path='outputs/test_bayley_cognitive_score_extract.pdf'
    )

    result = graph.invoke(initial_state)

    found_pages = result.get('found_pages', [])
    pages_data = result.get('pages', [])

    if found_pages:
        create_pdf_with_found_pages(found_pages, pages_data, result.get('out_path', 'outputs/test_sensory_score_extract.pdf'))
    else:
        print("No pages found to add the PDF")

if __name__ == "__main__":
    main() 