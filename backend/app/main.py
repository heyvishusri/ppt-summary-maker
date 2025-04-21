from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import shutil
import time # To create unique filenames if needed
from dotenv import load_dotenv

# Import the service functions
from app.services.parser import extract_text_from_file
from app.services.summarizer import summarize_text
from app.services.ppt_generator import create_summary_ppt

load_dotenv()

origins = [
    "http://localhost:3000",
]

app = FastAPI(title="PPT Summary Maker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories (Consider making these configurable via .env)
UPLOAD_DIRECTORY = "./temp_uploads"
OUTPUT_DIRECTORY = "./generated_ppts" # Directory for generated PPTs

# Ensure directories exist
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)


@app.get("/")
async def read_root():
    """ Root endpoint """
    return {"message": "Welcome to the PPT Summary Maker API!"}


@app.post("/summarize")
async def summarize_document_endpoint(file: UploadFile = File(...)):
    """
    Receives a document, extracts text, summarizes it, creates a PPT,
    and returns the summary text (for now).
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    allowed_content_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if file.content_type not in allowed_content_types:
        raise HTTPException(status_code=400, detail=f"Invalid file type: {file.content_type}. Only PDF and DOCX are allowed.")

    # --- 1. Save Uploaded File Temporarily ---
    # Use a more unique temporary filename to avoid conflicts
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    temp_filename = f"{timestamp}_{file.filename}"
    temp_file_path = os.path.join(UPLOAD_DIRECTORY, temp_filename)

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        print(f"Error saving uploaded file: {e}")
        raise HTTPException(status_code=500, detail=f"Could not save uploaded file: {file.filename}")
    finally:
        await file.close() # Close the upload stream

    extracted_text = ""
    summary = ""
    ppt_filepath = ""

    try:
        # --- 2. Parse Text from File ---
        print(f"Parsing file: {temp_file_path}")
        extracted_text = extract_text_from_file(temp_file_path)
        if not extracted_text:
            raise HTTPException(status_code=400, detail="Could not extract text from the document or the document is empty.")
        print(f"Extracted text length: {len(extracted_text)} characters")

        # --- 3. Summarize Text ---
        # Limit text sent to summarizer if too long (basic mitigation for now)
        # A better approach involves chunking in the summarizer service itself.
        MAX_CHARS_FOR_SUMMARY = 10000 # Example limit, adjust as needed
        text_to_summarize = extracted_text[:MAX_CHARS_FOR_SUMMARY]
        if len(extracted_text) > MAX_CHARS_FOR_SUMMARY:
             print(f"Warning: Input text truncated to {MAX_CHARS_FOR_SUMMARY} chars for summarization.")

        print("Starting summarization...")
        summary = summarize_text(text_to_summarize) # Using default min/max length from summarizer.py
        if not summary:
             raise HTTPException(status_code=500, detail="Failed to generate summary.")
        print("Summarization complete.")

        # --- 4. Generate PPT ---
        # (Note: In a real async app, this would happen later)
        print("Generating PPT...")
        ppt_filepath = create_summary_ppt(summary, file.filename, OUTPUT_DIRECTORY)
        print(f"PPT generated at: {ppt_filepath}")

        # --- 5. Return Result (Summary Text for Now) ---
        # TODO: Next step will be returning the PPT file itself for download.
        return {
            "message": "Document processed successfully.",
            "original_filename": file.filename,
            "summary": summary,
            "ppt_generated_at": ppt_filepath # Info for backend log/debug
        }

    except HTTPException as http_exc:
         # Re-raise HTTPExceptions directly
         raise http_exc
    except ValueError as val_err: # Catch specific errors like unsupported file type
         raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        # Catch-all for other unexpected errors during processing
        print(f"Error during processing: {e}")
        # In production, log the full error traceback
        raise HTTPException(status_code=500, detail=f"An error occurred during processing: {e}")

    finally:
        # --- 6. Cleanup ---
        # Delete the temporary uploaded file after processing
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                print(f"Cleaned up temporary file: {temp_file_path}")
            except OSError as e:
                print(f"Error deleting temporary file {temp_file_path}: {e}")
        # We keep the generated PPT for now, but you might add cleanup logic for it later.

# Reminder: Run with 'uvicorn app.main:app --reload --port 8000' from the 'backend' directory