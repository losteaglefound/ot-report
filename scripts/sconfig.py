import os
from pathlib import Path
import sys


class File:
    filename: str | None = None

    def __init__(self, file_path: str):
        self._file_path: str = file_path
        self.__check_file_exist()

        self.filename = os.path.basename(self._file_path)

    def __check_file_exist(self):
        if not os.path.exists(self._file_path):
            raise RuntimeError(f"File not found: {self._file_path}")

    def __repr__(self):
        return self._file_path

    def __str__(self):
        return self._file_path


class Config:
    BASE_DIR = Path(__file__).resolve().parent
    PROJECT_DIR = BASE_DIR.parent
    
    def get_input_file_pdf_image_file(self) -> File:
        return File(
            os.path.join(
                self.PROJECT_DIR,
                "assets",
                "inputs",
                "Bayley-image-4-Cognitive-Language-and-Motor-Scales-Score-Report_70360701_1751082282441.pdf"
            )
        )

config = Config()

sys.path.append(config.PROJECT_DIR.__str__())

    