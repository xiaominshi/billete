I will update the `database.py` file to filter the statistics calculations so that they only include entries where tickets have been issued (identified by the presence of "FA PAX" in the raw code).

Specific changes:
1.  **Modify `get_kpi_stats`**:
    -   Update the SQL queries for `total_searches` and `total_pax` to include the condition `AND code LIKE '%FA PAX%'`.
    -   This ensures that "Total Pax", "Avg Group Size", and the underlying "Total Searches" (interpreted as Ticketed Orders) only reflect confirmed bookings.

2.  **Modify `get_customer_stats`**:
    -   Update the SQL query to include `AND code LIKE '%FA PAX%'`.
    -   This ensures "Repeat Rate" and "Loyal Customer List" are derived exclusively from ticketed passengers.

I will use `LIKE '%FA PAX%'` as the filter condition, which corresponds to the standard indicator for issued tickets in the system.