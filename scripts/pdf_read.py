import asyncio

import pdfplumber


from sconfig import config as sconfig
from config import config as bconfig


async def main():
    file_path = sconfig.PROJECT_DIR / "assets/inputs/Bayley-4-Cognitive-Language-and-Motor-Scales-Score-Report_70360701_1751082282441.pdf"

    with pdfplumber.open(file_path) as p:
        for page in p.pages:
            print(page.extract_text())

if __name__ == "__main__":
    asyncio.run(main())