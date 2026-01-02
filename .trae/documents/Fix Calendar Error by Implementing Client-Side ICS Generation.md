To fix the "ICS generation requires flight data context" error, I will move the calendar generation logic from the server to the client (browser). 

**Reason for the error**: The server optimization we performed (stateless Logic) means the server no longer "remembers" the last processed flight data when you click the Calendar button.

**Solution**: Since the browser already has the flight data (in `lastProcessedData`) to display the results, we can generate the `.ics` file directly in JavaScript. This is faster and works without asking the server.

### Implementation Plan

1.  **Modify `templates/index.html`**:
    *   Locate the `downloadCalendar()` function.
    *   Replace the `window.location.href = '/download_ics'` call with JavaScript code that:
        *   Checks if `lastProcessedData` exists.
        *   Iterates through the flights in `lastProcessedData.flights`.
        *   Constructs a standard ICS (iCalendar) string format.
        *   Creates a `Blob` object and triggers a file download (`itinerary.ics`) directly in the browser.

### Expected Behavior
*   Clicking "Calendar" will instantly download the `.ics` file.
*   No network request is made.
*   The error message will disappear.
