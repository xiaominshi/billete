# Add QR Code Upload and Display Functionality

I will implement the QR code upload feature as requested. The uploaded QR code will be saved on the server and linked to the user's account. It will replace the default QR code in the flight itinerary card when the page loads.

## Implementation Steps

### 1. Database Update (`database.py`)
- **Schema Change**: Add a new column `qr_code` (TEXT) to the `users` table.
- **Migration**: Add logic in `init_db()` to automatically add this column to existing databases.
- **Helpers**: Add/Update functions to retrieve and update the user's QR code path.

### 2. Backend Logic (`server.py`)
- **File Storage**: Create a directory `static/qrcodes` to store user uploaded files.
- **Upload Route**: Create a new endpoint `/user/upload_qr` that:
    - Accepts an image file upload.
    - Saves it as `<user_id>_qrcode.png` (or original extension) in `static/qrcodes/`.
    - Updates the database with the file path.
- **Page Load**: Update the `home()` route (`/`) to:
    - Fetch the current user's `qr_code` path.
    - Pass this path to the `index.html` template.

### 3. Frontend Interface (`templates/index.html`)
- **Display**: Update the `#vc-qr-img` element to use the user's QR code if available, falling back to the default `/static/qrcode.jpg`.
- **Upload UI**: Add a "Upload QR Code" button (likely near the existing QR code or controls).
- **Interaction**: Add JavaScript to:
    - Trigger a hidden file input when the button is clicked.
    - Upload the file asynchronously to `/user/upload_qr`.
    - On success, immediately update the `#vc-qr-img` source to show the new QR code without reloading the page.
