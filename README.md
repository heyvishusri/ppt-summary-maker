# PPT Summary Maker (Async Basic Version)

A web application designed to automatically generate basic PowerPoint presentation summaries from uploaded PDF and DOCX documents. This project aims to reduce the manual effort required for document synthesis. Built with React for the frontend and Python/FastAPI for the backend.

**(Note: This is the v0.1 Async Basic version reflecting the current development stage.)**

## Table of Contents

-   [Features](#features)
-   [Technology Stack](#technology-stack)
-   [Folder Structure](#folder-structure)
-   [Prerequisites](#prerequisites)
-   [Setup](#setup)
-   [Running the Application](#running-the-application)
-   [API Endpoints](#api-endpoints)
-   [Current Limitations](#current-limitations)
-   [Future Enhancements](#future-enhancements)
-   [Contributing](#contributing)
-   [License](#license)

## Features

*   **File Upload:** Upload `.pdf` and `.docx` files via a web interface.
*   **Asynchronous Processing:** Handles document processing in the background using FastAPI's `BackgroundTasks`, providing immediate feedback to the user.
*   **Text Extraction:** Extracts text content from uploaded PDF (using PyMuPDF) and DOCX (using python-docx) files.
*   **NLP Summarization:** Generates abstractive summaries using a pre-trained Hugging Face Transformers model (`facebook/bart-large-cnn` by default).
*   **Basic PPT Generation:** Creates a simple `.pptx` file containing a title slide and a content slide with the generated summary (using python-pptx).
*   **Status Polling:** Frontend polls the backend to check the status of the processing task (Processing, Completed, Failed).
*   **Result Download:** Allows users to download the generated `.pptx` file upon successful completion.
*   **Basic Configuration:** Backend directory paths are configurable via a `.env` file.

## Technology Stack

*   **Frontend:**
    *   React (v18+)
    *   Axios (for API requests)
    *   CSS (basic styling)
*   **Backend:**
    *   Python (v3.8+)
    *   FastAPI (web framework)
    *   Uvicorn (ASGI server)
    *   PyMuPDF (PDF parsing)
    *   python-docx (DOCX parsing)
    *   python-pptx (PPTX generation)
    *   Transformers (Hugging Face library for NLP)
    *   PyTorch (or TensorFlow, required by Transformers)
    *   python-dotenv (for environment variables)

## Folder Structure

ppt-summary-maker/
├── .git/
├── .gitignore # Top-level ignore rules
├── backend/
│ ├── .env # Backend environment variables (GITIGNORED - Needs Creation)
│ ├── .gitignore # Backend specific ignore rules
│ ├── app/ # Main Python application code
│ │ ├── services/ # Service modules (parser, summarizer, etc.)
│ │ ├── init.py
│ │ └── main.py # FastAPI app definition and endpoints
│ ├── requirements.txt # Python dependencies
│ └── venv/ # Python virtual environment (GITIGNORED)
└── frontend/
├── .gitignore # Frontend specific ignore rules
├── node_modules/ # Frontend dependencies (GITIGNORED)
├── package.json # Frontend dependencies and scripts
├── public/ # Static assets (index.html, etc.)
└── src/ # React source code (App.js, etc.)
└── README.md # This file


## Prerequisites

*   **Python:** Version 3.8 or higher installed. ([python.org](https://python.org/)) Make sure `pip` is available and Python is added to your system's PATH.
*   **Node.js and npm:** Node.js LTS version recommended. npm is included with Node.js. ([nodejs.org](https://nodejs.org/))
*   **Git:** For cloning the repository. ([git-scm.com](https://git-scm.com/))

## Setup

1.  **Clone the Repository:**
    ```bash
    git clone <https://github.com/heyvishusri/ppt-summary-maker.git>
    cd ppt-summary-maker
    ```

2.  **Backend Setup:**
    *   Navigate to the backend directory:
        ```bash
        cd backend
        ```
    *   Create a Python virtual environment:
        ```bash
        python -m venv venv
        ```
    *   Activate the virtual environment:
        *   **Windows (Command Prompt/PowerShell):** `.\venv\Scripts\activate`
        *   **Windows (Git Bash):** `source venv/Scripts/activate`
        *   **macOS/Linux:** `source venv/bin/activate`
        *(You should see `(venv)` in your terminal prompt)*
    *   Install Python dependencies:
        ```bash
        pip install -r requirements.txt
        ```
        *(Note: This might take some time, especially downloading `torch` and `transformers`)*
    *   Create the environment file:
        *   Create a file named `.env` in the `backend` directory.
        *   Add the following (adjust paths if needed, but defaults are usually fine):
            ```dotenv
            UPLOAD_DIR=./temp_uploads
            OUTPUT_DIR=./generated_ppts
            ```

3.  **Frontend Setup:**
    *   Navigate to the frontend directory (from the project root):
        ```bash
        cd ../frontend
        # Or from backend: cd ../frontend
        ```
    *   Install Node.js dependencies:
        ```bash
        npm install
        ```

## Running the Application

You need to run both the backend and frontend servers simultaneously.

1.  **Run the Backend Server:**
    *   Open a terminal.
    *   Navigate to the `backend` directory (`cd path/to/ppt-summary-maker/backend`).
    *   Activate the virtual environment (e.g., `.\venv\Scripts\activate` on Windows).
    *   Start the FastAPI server using Uvicorn:
        ```bash
        uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
        ```
    *   The backend API will be running at `http://127.0.0.1:8000`. Leave this terminal running.
    *   *(The first time you run this after setup, the Transformers library might download the summarization model files, which can take time)*

2.  **Run the Frontend Server:**
    *   Open a **separate** terminal.
    *   Navigate to the `frontend` directory (`cd path/to/ppt-summary-maker/frontend`).
    *   Start the React development server:
        ```bash
        npm start
        ```
    *   This should automatically open the application in your default web browser at `http://localhost:3000`. Leave this terminal running.

3.  **Access the Application:**
    *   Open your web browser and navigate to `http://localhost:3000`.
    *   You should see the PPT Summary Maker interface. Use the "Choose File" button to upload a PDF or DOCX and click "Generate Summary PPT".

## API Endpoints

The backend provides the following RESTful API endpoints:

*   `GET /`: Root endpoint for basic API info/health check.
*   `POST /summarize`: Accepts `multipart/form-data` file upload. Returns `{"task_id": "..."}` (HTTP 202).
*   `GET /status/{task_id}`: Polls the status of a background task. Returns `{"status": "...", ...}` (HTTP 200 or 404).
*   `GET /download/{filename}`: Downloads the generated PPT file. Returns the file stream (HTTP 200 or 404).

## Current Limitations (v0.1)

*   **No User Authentication/Authorization:** The application is currently open to anyone who can access it.
*   **In-Memory Task State:** Task progress is stored in server memory and is lost if the backend server restarts. Not suitable for production reliability.
*   **`BackgroundTasks` Scalability:** Uses FastAPI's built-in background tasks, which may not scale well under heavy concurrent load compared to dedicated task queues (like Celery).
*   **No OCR:** Cannot process scanned (image-based) PDF documents.
*   **No Password Protection Handling:** Fails on password-protected files.
*   **Basic PPT Output:** Generates a very simple PPT structure; no templates, complex layouts, or branding.
*   **Long Document Truncation:** Very long documents might be truncated before summarization due to model input limits.
*   **Summarization Quality:** Dependent on the pre-trained model; may not be perfect for all document types or capture all nuances.
*   **No File Cleanup:** Generated PPT files in `backend/generated_ppts` are not automatically deleted.
*   **Limited Error Detail in UI:** While the backend logs errors, the UI error messages are relatively basic.

## Future Enhancements

*   Implement User Authentication & Authorization (Login/Register).
*   Integrate a persistent Task Queue (Celery + Redis/RabbitMQ).
*   Add OCR capability for scanned documents.
*   Handle password-protected files.
*   Implement chunking for reliable long document summarization.
*   Allow user control over summary length and style.
*   Enhance PPT generation with templates and layout options.
*   Add support for more input file formats.
*   Implement automated cleanup of old generated files.
*   Improve progress indication and error reporting in the UI.
*   Add a job history dashboard for users.
*   Develop automated tests (unit, integration).
---
