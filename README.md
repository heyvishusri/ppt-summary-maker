# PPT Summary Maker

A full-stack project for uploading documents, summarizing the content using NLP, and generating PowerPoint presentations.

## Project Structure

```
ppt-summary-maker/
├── .gitignore
├── backend/
│   ├── .env
│   ├── .gitignore
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py
│   ├── requirements.txt
│   └── venv/
└── frontend/
    ├── .gitignore
    ├── node_modules/
    ├── package.json
    ├── public/
    └── src/
```

## Tech Stack

- **Backend:** Python, FastAPI
- **Frontend:** React.js
- **Other Tools:** Node.js, npm, Python Virtual Environment, Git

## Setup Instructions

### Prerequisites

- Node.js and npm installed
- Python 3.7+ installed
- Git installed
- Visual Studio Code (recommended)

### Backend Setup

1. Navigate to the backend folder:

    ```bash
    cd backend
    ```

2. Create and activate a virtual environment:

    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Run the development server:

    ```bash
    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
    ```

5. API will be available at:  
   `http://127.0.0.1:8000`

6. API documentation (Swagger UI):  
   `http://127.0.0.1:8000/docs`

### Frontend Setup

1. Navigate to the frontend folder:

    ```bash
    cd frontend
    ```

2. Install dependencies:

    ```bash
    npm install
    ```

3. Start the development server:

    ```bash
    npm start
    ```

4. React app will run at:  
   `http://localhost:3000`

## Git Setup

Initialize Git (if not already done):

```bash
git init
```


