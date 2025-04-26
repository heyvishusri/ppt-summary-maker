from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
import uvicorn
import os
import shutil
import time
import uuid  # For generating unique task IDs
from dotenv import load_dotenv

# Import the service functions
from app.services.parser import extract_text_from_file
from app.services.summarizer import summarize_text
from app.services.ppt_generator import create_summary_ppt

load_dotenv()

origins = [
    "http://localhost:3000",
]

app = FastAPI(title="PPT Summary Maker API - Async")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories (Consider making these configurable via .env)
UPLOAD_DIRECTORY = "./temp_uploads"
OUTPUT_DIRECTORY = "./generated_ppts"  # Directory for generated PPTs

# Ensure directories exist
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

# --- In-Memory Task Status Tracking (Simple Example) ---
# WARNING: This is NOT production-ready. Statuses are lost on server restart.
# Use Redis, Celery results backend, or a database for persistence.
task_statuses = {}
# Example structure:
# task_statuses = {
#    "task-id-123": {"status": "PROCESSING"},
#    "task-id-456": {"status": "COMPLETED", "output_filename": "Summary_report.pptx"},
#    "task-id-789": {"status": "FAILED", "error": "Failed to parse document"},
# }
# ---


# --- Background Processing Function ---
def process_document_background(
    task_id: str, temp_file_path: str, original_filename: str
):
    """
    This function runs in the background to process the document.
    It updates the task_statuses dictionary upon completion or failure.
    """
    print(f"[Task {task_id}] Background processing started for: {original_filename}")
    extracted_text = ""
    summary = ""
    ppt_filepath = ""
    output_filename = ""

    try:
        # --- 1. Parse Text ---
        print(f"[Task {task_id}] Parsing file: {temp_file_path}")
        extracted_text = extract_text_from_file(temp_file_path)
        if not extracted_text:
            raise ValueError(
                "Could not extract text from the document or the document is empty."
            )
        print(
            f"[Task {task_id}] Extracted text length: {len(extracted_text)} characters"
        )

        # --- 2. Summarize Text ---
        MAX_CHARS_FOR_SUMMARY = 10000  # Example limit
        text_to_summarize = extracted_text[:MAX_CHARS_FOR_SUMMARY]
        if len(extracted_text) > MAX_CHARS_FOR_SUMMARY:
            print(
                f"[Task {task_id}] Warning: Input text truncated to {MAX_CHARS_FOR_SUMMARY} chars for summarization."
            )

        print(f"[Task {task_id}] Starting summarization...")
        # Update status to indicate summarization step (optional detail)
        # task_statuses[task_id] = {"status": "SUMMARIZING"}
        summary = summarize_text(text_to_summarize)
        if not summary:
            raise RuntimeError("Failed to generate summary (empty result).")
        print(f"[Task {task_id}] Summarization complete.")

        # --- 3. Generate PPT ---
        print(f"[Task {task_id}] Generating PPT...")
        # Update status (optional detail)
        # task_statuses[task_id] = {"status": "GENERATING_PPT"}
        ppt_filepath = create_summary_ppt(summary, original_filename, OUTPUT_DIRECTORY)
        output_filename = os.path.basename(ppt_filepath)
        print(f"[Task {task_id}] PPT generated at: {ppt_filepath}")

        # --- 4. Update Status to COMPLETED ---
        task_statuses[task_id] = {
            "status": "COMPLETED",
            "output_filename": output_filename,
            # "summary": summary # Optionally include summary if needed by frontend later
        }
        print(f"[Task {task_id}] Processing COMPLETED.")

    except Exception as e:
        # --- Handle Errors and Update Status to FAILED ---
        error_message = f"Processing failed: {e}"
        print(f"[Task {task_id}] {error_message}")
        task_statuses[task_id] = {"status": "FAILED", "error": str(e)}

    finally:
        # --- 5. Cleanup Temporary Uploaded File ---
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                print(f"[Task {task_id}] Cleaned up temporary file: {temp_file_path}")
            except OSError as e:
                print(
                    f"[Task {task_id}] Error deleting temporary file {temp_file_path}: {e}"
                )


# --- API Endpoints ---


@app.get("/")
async def read_root():
    """Root endpoint"""
    return {"message": "Welcome to the PPT Summary Maker API! (Async Version)"}


@app.post("/summarize", status_code=202)  # Use 202 Accepted status code
async def summarize_document_endpoint(
    background_tasks: BackgroundTasks,  # Inject BackgroundTasks
    file: UploadFile = File(...),
):
    """
    Accepts a document, saves it, schedules background processing,
    and returns a task ID immediately.
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    allowed_content_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]
    if file.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Only PDF and DOCX allowed.",
        )

    # --- 1. Save Uploaded File Temporarily with Unique Name ---
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    # Incorporate a unique ID in the temp filename in case of simultaneous uploads
    unique_id = uuid.uuid4().hex[:8]
    temp_filename = f"{timestamp}_{unique_id}_{file.filename}"
    temp_file_path = os.path.join(UPLOAD_DIRECTORY, temp_filename)

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        print(f"Error saving uploaded file: {e}")
        raise HTTPException(
            status_code=500, detail=f"Could not save uploaded file: {file.filename}"
        )
    finally:
        await file.close()

    # --- 2. Generate Task ID and Set Initial Status ---
    task_id = str(uuid.uuid4())
    task_statuses[task_id] = {"status": "PROCESSING"}  # Set initial status

    # --- 3. Add Background Task ---
    background_tasks.add_task(
        process_document_background,
        task_id,  # Pass task ID
        temp_file_path,  # Pass temp file path
        file.filename,  # Pass original filename
    )
    print(f"Task {task_id} scheduled for file: {file.filename}")

    # --- 4. Return Task ID Immediately ---
    return {"message": "Processing started.", "task_id": task_id}


@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Checks the status of a background task.
    """
    print(f"Status check requested for task: {task_id}")
    status_info = task_statuses.get(task_id)

    if not status_info:
        print(f"Status check failed: Task ID {task_id} not found.")
        raise HTTPException(status_code=404, detail="Task ID not found")

    print(f"Current status for task {task_id}: {status_info}")
    return status_info


@app.get("/download/{filename}")
async def download_ppt(filename: str):
    """
    Provides the generated PPT file for download. (No changes needed here)
    """
    if ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    file_path = os.path.join(OUTPUT_DIRECTORY, filename)

    if not os.path.exists(file_path):
        print(f"Download request failed: File not found at {file_path}")
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    print(f"Providing download for: {file_path}")
    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=filename,
    )
