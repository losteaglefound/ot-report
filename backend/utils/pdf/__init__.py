import os

from pdf2image import convert_from_path


def pdf_convert_to_image(
        file_path: str,
        session_dir: str
    ) -> str:
    """
    Convert input native pdf to image pdf.
    Args:
        file_path: input file path.
        session_dir: session dir path
    
    Returns:
        output (image pdf) file path.

    """
    basename = os.path.basename(file_path)
    basename = "image_" + basename
    output_path = os.path.join(session_dir, basename)

    images = convert_from_path(file_path)

    pages = []
    for i, image in enumerate(images):
        image_rgb = image.convert("RGB")
        pages.append(image_rgb)

    pages[0].save(output_path, "PDF", save_all=True, append_images=pages[1:])
    
    return output_path