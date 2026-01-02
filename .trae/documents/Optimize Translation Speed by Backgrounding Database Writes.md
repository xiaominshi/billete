To address the slow translation speed, I will optimize the server-side processing by making the database write operation asynchronous.

### Proposed Changes

1.  **Modify `server.py`**:
    *   Locate the `/process` route handler.
    *   Identify the `save_sync(current_logic)` call which currently blocks the response until the database write is complete.
    *   Wrap this call in a background thread using Python's `threading` module.
    *   This will allow the server to return the translation result to the frontend immediately, while the history saving happens in the background.

### Expected Behavior
*   **User Experience**: The "Processing..." loading overlay will disappear much faster after clicking "Translate".
*   **Backend**: The translation result is generated and returned immediately. The "Write to database" operation continues in the background without making the user wait.
*   **Reliability**: Error logging is already in place within the saving function, so any background errors will still be logged to the console.
