Great! I will implement the **Statistics Dashboard**.

### Plan:
1.  **Backend (`server.py` & `database.py`)**:
    -   Create a new API endpoint `/stats/detailed` that queries the database.
    -   It will return:
        -   Daily counts for the last 7 days.
        -   Top 5 most frequent airport pairs (Origin-Dest).
2.  **Frontend (`index.html`)**:
    -   Add `Chart.js` via CDN.
    -   Add a "📊 统计 (Stats)" button near the "History" section.
    -   Create a Modal (Pop-up) to display the chart and top routes list.
    -   Write the JS logic to fetch data and render the chart.

I will start by updating the database logic to support these queries.