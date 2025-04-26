import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";
const POLLING_INTERVAL = 3000; // Check status every 3 seconds

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [generatedFilename, setGeneratedFilename] = useState(null);
  const [currentTaskId, setCurrentTaskId] = useState(null); // Keep state for triggering effects/UI
  const pollingIntervalRef = useRef(null);
  const currentTaskIdRef = useRef(null); // *** ADD REF FOR TASK ID ***

  // --- Sync Task ID State to Ref ---
  // This effect runs whenever currentTaskId state changes
  useEffect(() => {
    currentTaskIdRef.current = currentTaskId; // Update the ref with the latest task ID
    console.log(`Task ID Ref updated: ${currentTaskIdRef.current}`);
  }, [currentTaskId]); // Dependency array ensures it runs when currentTaskId changes

  // --- Stop Polling Function ---
  const stopPolling = (caller = "UNKNOWN") => {
    if (pollingIntervalRef.current) {
      console.log(
        `>>> stopPolling called by: ${caller}. Clearing interval ID: ${pollingIntervalRef.current}`
      );
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    } else {
      console.log(
        `>>> stopPolling called by: ${caller}, but no active interval found.`
      );
    }
  };

  // --- Cleanup polling on component unmount ---
  useEffect(() => {
    // This effect runs only once on mount
    console.log("App Component Mounted");
    return () => {
      // This cleanup function runs on unmount
      console.log("App Component Unmounting - Cleaning up polling.");
      stopPolling("UNMOUNT");
    };
  }, []); // Empty dependency array

  // --- File Selection Handler ---
  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
    setMessage("");
    setGeneratedFilename(null);
    setIsLoading(false);
    stopPolling("FILE_CHANGE");
    setCurrentTaskId(null); // Reset state
  };

  // --- Polling Function ---
  const pollTaskStatus = async (taskId) => {
    // Defend against race conditions: Check if polling should still be active
    if (!pollingIntervalRef.current) {
      console.log(
        `Polling check for task ${taskId}, but polling interval is not active. Aborting check.`
      );
      return;
    }
    // Also check if the task being polled is still the relevant one
    if (taskId !== currentTaskIdRef.current) {
      console.warn(
        `Polling check for task ${taskId}, but active task ref is ${currentTaskIdRef.current}. Aborting check.`
      );
      return;
    }

    console.log(`Polling status check for task: ${taskId}`);
    try {
      const response = await axios.get(`${API_BASE_URL}/status/${taskId}`);
      const statusInfo = response.data;
      console.log(`Status Response for ${taskId}:`, statusInfo);

      // Double-check task ID *after* getting response, before updating state
      if (taskId !== currentTaskIdRef.current) {
        console.warn(
          `Received status for task ${taskId}, but active task ref changed to ${currentTaskIdRef.current} during request. Ignoring status.`
        );
        return;
      }

      if (statusInfo.status === "COMPLETED") {
        console.log(`Status is COMPLETED for task ${taskId}.`);
        stopPolling("COMPLETED");
        setIsLoading(false); // Update state
        setMessage("Processing completed successfully!"); // Update state
        setGeneratedFilename(statusInfo.output_filename); // Update state
        // No need to reset currentTaskId state here, can be useful for debugging
      } else if (statusInfo.status === "FAILED") {
        console.log(`Status is FAILED for task ${taskId}.`);
        stopPolling("FAILED");
        setIsLoading(false); // Update state
        setMessage(
          `Error: Processing failed - ${statusInfo.error || "Unknown error"}`
        ); // Update state
        // Maybe clear task ID state on failure? Optional.
        // setCurrentTaskId(null);
      } else {
        // Status is PROCESSING or similar
        console.log(
          `Status is ${statusInfo.status} for task ${taskId}. Continuing polling.`
        );
        // Only update message if the UI should still show processing
        if (isLoading) {
          // Check isLoading state
          setMessage(`Status: ${statusInfo.status}...`);
        }
      }
    } catch (error) {
      console.error(`Error polling status for task ${taskId}:`, error);
      // Only handle errors if they pertain to the *currently active* task
      if (taskId === currentTaskIdRef.current) {
        if (error.response && error.response.status === 404) {
          setMessage(
            "Error: Task ID not found on server. Please try uploading again."
          );
          stopPolling("STATUS_404_ERROR");
          setIsLoading(false);
          setCurrentTaskId(null); // Clear state if task is gone
        } else {
          setMessage("Error checking status. Check console.");
          // Decide whether to stop polling on other errors
          // stopPolling('STATUS_OTHER_ERROR');
          // setIsLoading(false); // Maybe set loading false on error?
        }
      } else {
        console.warn(
          `Error occurred while polling for task ${taskId}, but it's no longer the active task (${currentTaskIdRef.current}). Ignoring error for polling control.`
        );
      }
    }
  };

  // --- Upload Handler ---
  const handleUpload = async () => {
    if (!selectedFile) {
      setMessage("Please select a file first.");
      return;
    }
    stopPolling("UPLOAD_START"); // Stop previous polling first

    // Reset state for the new upload
    setMessage("Uploading file...");
    setIsLoading(true);
    setGeneratedFilename(null);
    setCurrentTaskId(null); // Ensure state starts clean

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await axios.post(`${API_BASE_URL}/summarize`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const { task_id } = response.data;
      console.log("Received Task ID:", task_id);

      if (task_id) {
        // Set state immediately - this triggers the useEffect to update the ref
        setCurrentTaskId(task_id);
        setMessage("Status: PROCESSING...");

        // Start polling immediately using the received task_id
        // (The ref might not be updated yet, but this first call is okay)
        pollTaskStatus(task_id);

        // Clear any previous interval robustly
        if (pollingIntervalRef.current) {
          console.warn(
            "Clearing unexpected existing interval before setting new one."
          );
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }

        // Set up interval polling
        console.log(`Setting up polling interval for task: ${task_id}`);
        pollingIntervalRef.current = setInterval(() => {
          // *** READ FROM THE REF INSIDE INTERVAL ***
          const taskIdFromRef = currentTaskIdRef.current;
          if (taskIdFromRef) {
            pollTaskStatus(taskIdFromRef); // Poll using the ID from the ref
          } else {
            // This check might be less critical now, but good safeguard
            console.warn(
              "Polling interval running but Task ID Ref is null/empty. Stopping poll."
            );
            stopPolling("INTERVAL_REF_NULL");
          }
        }, POLLING_INTERVAL);
        console.log(`Interval ID ${pollingIntervalRef.current} set.`);
      } else {
        throw new Error("Backend did not return a task_id.");
      }
    } catch (error) {
      console.error("Error starting upload:", error);
      stopPolling("UPLOAD_ERROR");
      setIsLoading(false);
      setCurrentTaskId(null); // Clear state on error
      if (error.response) {
        setMessage(
          `Error: ${
            error.response.data.detail || "Could not start processing."
          }`
        );
      } else if (error.request) {
        setMessage("Error: No response from server.");
      } else {
        setMessage(`Error: ${error.message}`);
      }
    }
  };

  // --- Get Download URL ---
  const getDownloadUrl = () => {
    if (!generatedFilename) return null;
    return `${API_BASE_URL}/download/${encodeURIComponent(generatedFilename)}`;
  };

  // --- UI Rendering ---
  return (
    <div className="App">
      <header className="App-header">
        {/* ... same JSX as before ... */}
        <h1>PPT Summary Maker (Async)</h1>
        <div>
          <input
            type="file"
            onChange={handleFileChange}
            accept=".pdf,.docx"
            disabled={isLoading}
          />
          <button onClick={handleUpload} disabled={isLoading || !selectedFile}>
            {isLoading ? "Processing..." : "Generate Summary PPT"}
          </button>
        </div>
        {message && (
          <p
            style={{
              color: message.toLowerCase().includes("error")
                ? "red"
                : "lightblue",
              marginTop: "20px",
            }}
          >
            {message}
          </p>
        )}
        {generatedFilename && !isLoading && (
          <div style={{ marginTop: "20px" }}>
            <a href={getDownloadUrl()} download>
              {" "}
              Download Generated PPT ({generatedFilename}){" "}
            </a>
          </div>
        )}
        {/* Optionally display task ID for debugging */}
        {/* {currentTaskId && <p style={{fontSize: '12px', color: 'grey'}}>Task ID: {currentTaskIdRef.current}</p>} */}
      </header>
    </div>
  );
}

// Add styles if missing
const styles = ` a[download] { padding: 10px 20px; font-size: 16px; cursor: pointer; background-color: #61dafb; color: #282c34; text-decoration: none; border-radius: 5px; display: inline-block; } `;
const styleSheet = document.createElement("style");
styleSheet.type = "text/css";
styleSheet.innerText = styles;
document.head.appendChild(styleSheet);

export default App;
