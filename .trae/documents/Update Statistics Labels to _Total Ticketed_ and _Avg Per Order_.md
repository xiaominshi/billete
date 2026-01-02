I will update the UI labels in `index.html` to reflect that the statistics are based on issued tickets.

1.  **Modify `index.html`**:
    *   Update Chinese translations:
        *   Change `kpi_pax_label` from "总乘客" to "**总出票人数**" (Total Ticketed Passengers).
        *   Change `kpi_avg_label` from "平均人数" to "**平均每单出票人数**" (Average Passengers Per Order).
    *   Update English/Spanish translations to match the new meaning (e.g., "Total Ticketed Pax", "Avg Pax / Order").
2.  **Verification**:
    *   I will not need to restart the server for HTML template changes (Flask debug mode is on), but I will refresh the page logic if needed. Since it's a template change, a simple refresh by the user is usually enough, but I will double check.

This will make the statistics dashboard clearly indicate that the numbers represent actual ticketed passengers and group sizes, not just search queries.