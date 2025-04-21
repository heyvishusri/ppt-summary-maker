import fitz  # PyMuPDF
from docx import Document
import os

def extract_text_from_file(file_path: str) -> str:
    """
    Extracts text content from a given file path (supports PDF and DOCX).

    Args:
        file_path: The path to the document file.

    Returns:
        The extracted text content as a single string.

    Raises:
        ValueError: If the file type is not supported or the file doesn't exist.
        Exception: For other potential errors during parsing.
    """
    if not os.path.exists(file_path):
        raise ValueError(f"File not found at path: {file_path}")

    _, file_extension = os.path.splitext(file_path.lower())
    text_content = ""

    try:
        if file_extension == ".pdf":
            doc = fitz.open(file_path)
            for page in doc:
                text_content += page.get_text()
            doc.close()
        elif file_extension == ".docx":
            doc = Document(file_path)
            for para in doc.paragraphs:
                text_content += para.text + "\n" # Add newline between paragraphs
        else:
            raise ValueError(f"Unsupported file type: {file_extension}. Only .pdf and .docx are supported.")

        return text_content.strip() # Remove leading/trailing whitespace

    except Exception as e:
        # Log the error in a real application
        print(f"Error parsing file {file_path}: {e}")
        # Re-raise a more specific exception or a generic one
        raise Exception(f"Failed to parse document: {os.path.basename(file_path)}") from e