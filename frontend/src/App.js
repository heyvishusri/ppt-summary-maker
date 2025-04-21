import React, { useState } from "react";
import axios from "axios"; // Import axios
import "./App.css"; // Keep basic styling

function App() {
  // State to hold the selected file
  const [selectedFile, setSelectedFile] = useState(null);
  // State to store messages from the backend
  const [message, setMessage] = useState("");
  // State to track loading status
  const [isLoading, setIsLoading] = useState(false);
  // State to hold the summary text
  const [summaryText, setSummaryText] = useState("");

  // Function to handle file selection from the input
  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]); // Get the first file selected
    setMessage(""); // Clear previous messages
  };

  // Function to handle the file upload
  const handleUpload = async () => {
    if (!selectedFile) {
      setMessage("Please select a file first.");
      return;
    }

    // Create a FormData object to send the file
    const formData = new FormData();
    formData.append("file", selectedFile); // 'file' must match the key expected by FastAPI (UploadFile = File(...))

    setMessage("Uploading...");
    setIsLoading(true);

    try {
      // Make the POST request to the backend API endpoint
      // Ensure the backend server is running on http://127.0.0.1:8000
      const response = await axios.post(
        "http://127.0.0.1:8000/summarize",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data", // Important for file uploads
          },
        }
      );

      // Handle successful response
      setMessage(response.data.message || "Upload successful!"); // Display message from backend
      setSummaryText(response.data.summary || ""); // Store the summary
      console.log("Backend Response:", response.data); // Log the full response for debugging
    } catch (error) {
      // Handle errors
      console.error("Error uploading file:", error);
      if (error.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        console.error("Error data:", error.response.data);
        console.error("Error status:", error.response.status);
        setMessage(
          `Error: ${error.response.data.detail || "Could not upload file."}`
        );
      } else if (error.request) {
        // The request was made but no response was received
        console.error("Error request:", error.request);
        setMessage("Error: Could not connect to the server. Is it running?");
      } else {
        // Something happened in setting up the request that triggered an Error
        console.error("Error message:", error.message);
        setMessage(`Error: ${error.message}`);
      }
    } finally {
      setIsLoading(false); // Set loading to false whether success or error
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>PPT Summary Maker</h1>
        <div>
          {/* File input */}
          <input type="file" onChange={handleFileChange} accept=".pdf,.docx" />

          {/* Upload button - disabled while loading */}
          <button onClick={handleUpload} disabled={isLoading}>
            {isLoading ? "Uploading..." : "Upload and Summarize (Test)"}
          </button>
        </div>

        {/* Display messages */}
        {message && (
          <p
            style={{
              color: message.startsWith("Error:") ? "red" : "lightgreen",
            }}
          >
            {message}
          </p>
        )}

        {/* Optionally display selected file name */}
        {selectedFile && <p>Selected file: {selectedFile.name}</p>}

        {/* Display Summary */}
        {summaryText && (
          <div
            style={{
              marginTop: "20px",
              padding: "10px",
              border: "1px solid white",
              textAlign: "left",
              maxWidth: "80%",
            }}
          >
            <h3>Generated Summary:</h3>
            <p style={{ whiteSpace: "pre-wrap", color: "white" }}>
              {summaryText}
            </p>{" "}
            {/* Use pre-wrap to respect newlines */}
          </div>
        )}
      </header>
    </div>
  );
}

export default App;
