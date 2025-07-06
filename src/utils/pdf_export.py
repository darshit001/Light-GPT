from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from datetime import datetime

def export_chat_to_pdf(messages):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 72, "MCP Assistant Chat History")
    
    c.setFont("Helvetica", 10)
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.drawString(72, height - 95, f"Exported on: {current_date}")
    
    c.line(72, height - 110, width - 72, height - 110)
    
    y_position = height - 140
    c.setFont("Helvetica-Bold", 11)
    
    for message in messages:
        role = "User" if message['role'] == 'user' else "Assistant"
        content = message['content']
        timestamp = message.get('timestamp', '')
        
        c.setFillColorRGB(0.2, 0.2, 0.8) if role == "User" else c.setFillColorRGB(0.2, 0.6, 0.2)
        c.drawString(72, y_position, f"{role} - {timestamp}")
        y_position -= 20
        
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 10)
        
        content_lines = content.split("\n")
        for line in content_lines:
            text_width = width - 144
            chars_per_line = int((text_width / 7) * 1.8)
            
            while len(line) > chars_per_line:
                space_pos = line[:chars_per_line].rfind(' ')
                if space_pos == -1:
                    space_pos = chars_per_line
                c.drawString(72, y_position, line[:space_pos])
                line = line[space_pos:].lstrip()
                y_position -= 14
                if y_position < 72:
                    c.showPage()
                    y_position = height - 72
                    c.setFont("Helvetica", 10)
            
            if line:
                c.drawString(72, y_position, line)
                y_position -= 14
            if y_position < 72:
                c.showPage()
                y_position = height - 72
                c.setFont("Helvetica", 10)
        
        y_position -= 10
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.line(72, y_position, width - 72, y_position)
        y_position -= 20
        if y_position < 72:
            c.showPage()
            y_position = height - 72
            c.setFont("Helvetica", 10)
    
    c.save()
    buffer.seek(0)
    return buffer.getvalue()