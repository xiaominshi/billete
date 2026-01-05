import io
import os
import datetime
import hashlib

# Monkey Patch for ReportLab < 3.6 on Python 3.7+ (Fixes "openssl_md5() takes no keyword arguments")
_original_md5 = hashlib.md5
def md5_fix(*args, **kwargs):
    if 'usedforsecurity' in kwargs:
        del kwargs['usedforsecurity']
    return _original_md5(*args, **kwargs)
hashlib.md5 = md5_fix

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.platypus import Table, TableStyle, Image as PlatypusImage

# --- Color & Style Definitions ---
COLOR_PRIMARY = HexColor('#2c3e50')    # Deep Blue/Gray for Headers
COLOR_TEXT_MAIN = HexColor('#34495e')  # Dark Gray for main text
COLOR_TEXT_LIGHT = HexColor('#7f8c8d') # Light Gray for secondary info
COLOR_BG_LIGHT = HexColor('#f8f9fa')   # Very light gray for backgrounds
COLOR_BORDER = HexColor('#bdc3c7')     # Light border color

def draw_plane_icon(c, x, y, size=10):
    """Draws a simple vector plane icon centered at (x,y)"""
    c.saveState()
    c.translate(x, y)
    s = size / 20.0 
    c.scale(s, s)
    # Simple plane path
    path = c.beginPath()
    path.moveTo(-10, 0)
    path.lineTo(5, 0)     # Body
    path.moveTo(-2, 0)
    path.lineTo(-6, 8)    # Wing 1
    path.lineTo(2, 0)
    path.lineTo(-6, -8)   # Wing 2
    path.lineTo(-2, 0)
    path.moveTo(5, 0)
    path.lineTo(8, 0)     # Nose
    
    c.setLineWidth(2)
    c.setStrokeColor(COLOR_PRIMARY)
    c.drawPath(path, stroke=1, fill=0)
    c.restoreState()

# Register a font that supports Chinese
# Using a fallback strategy if specific font files are not found
try:
    # Try to load a font commonly available or included in the project
    # Ideally, we should ship a font like 'NotoSansSC-Regular.ttf' in a fonts/ folder
    # For now, we'll assume a standard Windows font or a bundled one
    # If on Render (Linux), we might need to download/bundle one.
    
    # Check for bundled font
    FONT_PATH = os.path.join(os.path.dirname(__file__), "fonts", "SimHei.ttf")
    if not os.path.exists(FONT_PATH):
        # Fallback to Windows system font for local dev
        FONT_PATH = "C:\\Windows\\Fonts\\simhei.ttf"
    
    if os.path.exists(FONT_PATH):
        pdfmetrics.registerFont(TTFont('SimHei', FONT_PATH))
        FONT_NAME = 'SimHei'
    else:
        # Fallback to standard PDF font (no Chinese support) if font not found
        # This is critical to fix for production
        print("Warning: Chinese font not found. Using Helvetica.")
        FONT_NAME = 'Helvetica'
except Exception as e:
    print(f"Font loading error: {e}")
    FONT_NAME = 'Helvetica'

def generate_pdf(data, qr_code_path=None):
    """
    Generates a PDF itinerary based on structured data.
    data: dict containing 'passengers', 'flights', 'luggage'
    qr_code_path: path or url to user's QR code image
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # --- Header ---
    # Logo (Placeholder or actual file)
    logo_path = os.path.join(os.path.dirname(__file__), "static", "images", "logo.png") # Assume we might have one
    if os.path.exists(logo_path):
        c.drawImage(logo_path, 2*cm, height - 3*cm, width=4*cm, preserveAspectRatio=True, mask='auto')
    # else:
    #    # Draw text logo removed per request
    #    c.setFont(FONT_NAME, 24)
    #    c.drawString(2*cm, height - 2.5*cm, "BILLETE")
        
    c.setFont(FONT_NAME, 16)
    c.drawRightString(width - 2*cm, height - 2.5*cm, "电子行程单 / ITINERARY")
    
    c.setLineWidth(1)
    c.line(2*cm, height - 3.2*cm, width - 2*cm, height - 3.2*cm)
    
    y = height - 4.5*cm
    
    # --- Passengers ---
    c.setFont(FONT_NAME, 15)
    c.setFillColor(COLOR_PRIMARY)
    c.drawString(2*cm, y, "旅客信息 / Passengers")
    c.setFillColor(colors.black)
    y -= 0.8*cm
    
    pax_data = [["序号 / No.", "姓名 / Name", "票号 / Ticket Number"]]
    for idx, p in enumerate(data.get('passengers', [])):
        name = p['name'] if isinstance(p, dict) else str(p)
        ticket = p.get('ticket', '') if isinstance(p, dict) else ''
        pax_data.append([str(idx + 1), name, ticket])
        
    t_pax = Table(pax_data, colWidths=[2*cm, 8*cm, 7*cm])
    t_pax.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
        ('TEXTCOLOR', (0,0), (-1,-1), COLOR_TEXT_MAIN),
        ('GRID', (0,0), (-1,-1), 0.5, COLOR_BORDER),
        ('BACKGROUND', (0,0), (-1,0), COLOR_PRIMARY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTSIZE', (0,0), (-1,0), 11),  # Header Font Size
        ('FONTSIZE', (0,1), (-1,-1), 10), # Content Font Size
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('PADDING', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (1,0), (-1,-1), [colors.white, COLOR_BG_LIGHT]), # Zebra striping
    ]))
    t_pax.wrapOn(c, width, height)
    t_pax.drawOn(c, 2*cm, y - (len(pax_data) * 0.9 * cm)) # Approx height calc
    
    y -= (len(pax_data) * 0.9 * cm) + 1.5*cm
    
    # --- Flights ---
    c.setFont(FONT_NAME, 15)
    c.setFillColor(COLOR_PRIMARY)
    c.drawString(2*cm, y, "航班信息 / Flight Details")
    c.setFillColor(colors.black)
    y -= 1*cm
    
    flights = data.get('flights', [])
    for f in flights:
        # Check for page break
        if y < 6*cm:
            c.showPage()
            y = height - 3*cm
            c.setFont(FONT_NAME, 15)
            c.setFillColor(COLOR_PRIMARY)
            c.drawString(2*cm, y + 1*cm, "航班信息 / Flight Details") # Re-draw header if page break
            c.setFillColor(colors.black)
        
        # Flight Card Background (Rounded)
        card_height = 3.5*cm
        center_y = y - (card_height / 2) # Vertical center of the card
        
        c.setStrokeColor(COLOR_BORDER)
        c.setFillColor(colors.white)
        c.roundRect(2*cm, y-card_height, width-4*cm, card_height, 8, fill=1, stroke=1)
        
        # --- Left Column: Date & Airline ---
        c.setFillColor(COLOR_TEXT_MAIN)
        
        # Flight No (Large)
        c.setFont(FONT_NAME, 14) 
        c.drawString(3*cm, center_y + 0.4*cm, f.get('id', 'Flight'))
        
        # Date (Smaller, gray)
        c.setFillColor(COLOR_TEXT_LIGHT)
        c.setFont(FONT_NAME, 10)
        date_str = f"{f.get('year')}-{f.get('month')}-{f.get('day')}"
        c.drawString(3*cm, center_y - 0.5*cm, date_str)
        
        # --- Center Column: Route & Times ---
        c.setFillColor(COLOR_TEXT_MAIN)
        
        # Calculate visual centers for Origin and Dest relative to card center
        # Plane is at width/2
        # Origin block center: width/2 - 4cm
        # Dest block center: width/2 + 4cm
        
        origin_center_x = width/2 - 3.5*cm
        dest_center_x = width/2 + 3.5*cm
        
        # Origin Time & City
        c.setFont(FONT_NAME, 16) # Big Time
        c.drawCentredString(origin_center_x, center_y + 0.3*cm, f.get('start'))
        
        c.setFont(FONT_NAME, 11) # Small City
        c.setFillColor(COLOR_TEXT_LIGHT)
        c.drawCentredString(origin_center_x, center_y - 0.5*cm, f.get('origin'))
        
        # Plane Icon in Center
        draw_plane_icon(c, width/2, center_y + 0.3*cm, size=20)
        
        # Duration Text below plane
        c.setFont(FONT_NAME, 9)
        c.setFillColor(COLOR_TEXT_LIGHT)
        c.drawCentredString(width/2, center_y - 0.6*cm, f.get('duration', ''))

        # Dest Time & City
        c.setFillColor(COLOR_TEXT_MAIN)
        c.setFont(FONT_NAME, 16) # Big Time
        c.drawCentredString(dest_center_x, center_y + 0.3*cm, f.get('end'))
        
        # +1 Indicator
        if f.get('next_day'):
             c.setFont(FONT_NAME, 9)
             c.setFillColor(colors.red)
             # Place nicely next to time or above
             c.drawString(dest_center_x + 1.5*cm, center_y + 0.6*cm, "+1")

        c.setFont(FONT_NAME, 11) # Small City
        c.setFillColor(COLOR_TEXT_LIGHT)
        c.drawCentredString(dest_center_x, center_y - 0.5*cm, f.get('dest'))
        
        y -= (card_height + 0.5*cm) # Move down for next flight
        
    # --- Luggage ---
    if y < 4*cm:
        c.showPage()
        y = height - 3*cm

    lug = data.get('luggage', {})
    if lug:
        c.setFont(FONT_NAME, 15)
        c.setFillColor(COLOR_PRIMARY)
        c.drawString(2*cm, y, "行李额度 / Baggage Allowance")
        c.setFillColor(colors.black)
        y -= 0.8*cm
        
        # Luggage Box
        c.setStrokeColor(COLOR_BORDER)
        c.setFillColor(COLOR_BG_LIGHT)
        c.roundRect(2*cm, y-1.5*cm, width-4*cm, 1.5*cm, 4, fill=1, stroke=1)
        
        lug_text = f"托运行李: {lug.get('pack_count', 0)}件 x {lug.get('pack_weight', 0)}kg   |   手提行李: {lug.get('hand_count', 0)}件 x {lug.get('hand_weight', 0)}kg"
        c.setFillColor(COLOR_TEXT_MAIN)
        c.setFont(FONT_NAME, 11)
        c.drawString(2.5*cm, y-1*cm, lug_text)
        y -= 2*cm

    # --- Footer / QR Code ---
    # Draw at bottom of current page
    footer_y = 1.5*cm
    
    # Divider
    c.setStrokeColor(COLOR_BORDER)
    c.setLineWidth(0.5)
    c.line(2*cm, footer_y + 2.5*cm, width-2*cm, footer_y + 2.5*cm)
    
    if qr_code_path and qr_code_path.startswith('data:image'):
        try:
            # Handle Data URI
            import base64
            from PIL import Image as PILImage
            
            header, encoded = qr_code_path.split(",", 1)
            # data is already a local variable in this scope (from function argument), rename to qr_bytes
            qr_bytes = base64.b64decode(encoded)
            
            # Save temp file
            temp_qr = "temp_qr_pdf.png"
            with open(temp_qr, "wb") as f:
                f.write(qr_bytes)

                
            c.drawImage(temp_qr, 2*cm, footer_y, width=2.5*cm, height=2.5*cm)
            
            # Clean up later or rely on OS
        except Exception as e:
            print(f"QR Draw Error: {e}")
    
    c.setFont(FONT_NAME, 10)
    c.setFillColor(COLOR_PRIMARY)
    c.drawRightString(width-2*cm, footer_y + 1.5*cm, "祝您旅途愉快! / Have a nice trip!")
    
    c.setFont(FONT_NAME, 8)
    c.setFillColor(COLOR_TEXT_LIGHT)
    c.drawRightString(width-2*cm, footer_y + 1*cm, "如有疑问请联系客服 / Contact support for questions")
    c.drawRightString(width-2*cm, footer_y + 0.6*cm, "Generated by Billete System")
    
    c.save()
    buffer.seek(0)
    return buffer
