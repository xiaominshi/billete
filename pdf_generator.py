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
from reportlab.platypus import Table, TableStyle, Image as PlatypusImage

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
    c.drawString(2*cm, y, "旅客信息 / Passengers")
    y -= 0.8*cm
    
    pax_data = [["序号 / No.", "姓名 / Name", "票号 / Ticket Number"]]
    for idx, p in enumerate(data.get('passengers', [])):
        name = p['name'] if isinstance(p, dict) else str(p)
        ticket = p.get('ticket', '') if isinstance(p, dict) else ''
        pax_data.append([str(idx + 1), name, ticket])
        
    t_pax = Table(pax_data, colWidths=[2*cm, 8*cm, 7*cm])
    t_pax.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), FONT_NAME),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    t_pax.wrapOn(c, width, height)
    t_pax.drawOn(c, 2*cm, y - (len(pax_data) * 0.8 * cm)) # Approx height calc
    
    y -= (len(pax_data) * 0.8 * cm) + 1.5*cm
    
    # --- Flights ---
    c.setFont(FONT_NAME, 15)
    c.drawString(2*cm, y, "航班信息 / Flight Details")
    y -= 1*cm
    
    flights = data.get('flights', [])
    for f in flights:
        # Check for page break
        if y < 6*cm:
            c.showPage()
            y = height - 3*cm
            c.setFont(FONT_NAME, 15)
        
        # Flight Header Box
        c.setFillColor(colors.aliceblue)
        c.rect(2*cm, y-3*cm, width-4*cm, 3*cm, fill=1, stroke=0)
        c.setFillColor(colors.black)
        
        # Date & Flight No
        c.setFont(FONT_NAME, 11)
        date_str = f"{f.get('year')}年{f.get('month')}月{f.get('day')}日"
        c.drawString(2.5*cm, y-1*cm, date_str)
        c.drawRightString(width-2.5*cm, y-1*cm, f.get('id', 'Flight'))
        
        # Route
        c.setFont(FONT_NAME, 13)
        c.drawString(2.5*cm, y-2*cm, f"{f.get('start')} {f.get('origin')}")
        
        # Arrow / Duration
        c.setFont(FONT_NAME, 9)
        # Use simple ASCII arrow instead of unicode plane to ensure compatibility
        c.drawCentredString(width/2, y-1.8*cm, "-----------------------------------")
        c.drawCentredString(width/2, y-2.2*cm, f.get('duration', ''))
        
        c.setFont(FONT_NAME, 13)
        c.drawRightString(width-2.5*cm, y-2*cm, f"{f.get('dest')} {f.get('end')}")
        
        # Arrival Date hint
        if f.get('next_day'):
            c.setFont(FONT_NAME, 10)
            c.drawRightString(width-2.5*cm, y-2.5*cm, "(+1天到达)")
            
        y -= 3.5*cm # Move down for next flight
        
    # --- Luggage ---
    if y < 4*cm:
        c.showPage()
        y = height - 3*cm

    lug = data.get('luggage', {})
    if lug:
        c.setFont(FONT_NAME, 15)
        c.drawString(2*cm, y, "行李额度 / Baggage Allowance")
        y -= 0.8*cm
        
        lug_text = f"托运行李: {lug.get('pack_count', 0)}件 x {lug.get('pack_weight', 0)}kg   |   手提行李: {lug.get('hand_count', 0)}件 x {lug.get('hand_weight', 0)}kg"
        c.setFont(FONT_NAME, 10)
        c.drawString(2.5*cm, y, lug_text)
        y -= 1.5*cm

    # --- Footer / QR Code ---
    # Draw at bottom of current page
    footer_y = 2*cm
    
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

                
            c.drawImage(temp_qr, 2*cm, footer_y, width=3*cm, height=3*cm)
            
            # Clean up later or rely on OS
        except Exception as e:
            print(f"QR Draw Error: {e}")
    
    c.setFont(FONT_NAME, 10)
    c.drawRightString(width-2*cm, footer_y + 1*cm, "祝您旅途愉快! / Have a nice trip!")
    c.drawRightString(width-2*cm, footer_y + 0.5*cm, "Generated by Billete System")
    
    c.save()
    buffer.seek(0)
    return buffer
