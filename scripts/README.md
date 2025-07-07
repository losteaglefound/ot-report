# OCR Agent Scripts

This directory contains simple usage scripts for the OCR agent.

## Scripts

### `test_ocr_agent.py`
Interactive script that prompts for an image path and extracts text.

```bash
python scripts/test_ocr_agent.py
```

### `simple_ocr_test.py`
Basic usage example with minimal code.

```bash
python scripts/simple_ocr_test.py
```

## Usage

1. Make sure you have your OpenAI API key set up in environment variables:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

2. Run either script:
   ```bash
   python scripts/test_ocr_agent.py
   ```

3. Provide the path to an image file when prompted (JPG, PNG, etc.)

4. The script will extract and display the text from the image.

## Requirements

- OpenAI API key
- Image file (JPG, PNG, GIF, etc.)
- Required Python packages (see requirements.txt) 