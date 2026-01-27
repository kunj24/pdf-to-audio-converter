from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os

def create_sample_pdf():
    """Create a sample PDF for testing the PDF-to-audio converter."""
    output_path = "sample.pdf"
    
    # Create a new PDF with ReportLab
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Add some sample text
    c.setFont("Helvetica", 16)
    c.drawString(100, height - 100, "PDF to Audio Converter Test")
    
    c.setFont("Helvetica", 12)
    y_position = height - 150
    
    sample_text = [
        "This is a sample PDF document created for testing the PDF-to-audio converter.",
        "",
        "The converter extracts text from PDF files and converts it to spoken audio",
        "using Windows built-in text-to-speech voices.",
        "",
        "Key features include:",
        "- Extracting text from multiple pages",
        "- Cleaning up layout artifacts like hyphenation",
        "- Converting to WAV or MP3 format",
        "- Adjustable speech rate and voice selection",
        "",
        "This tool is particularly useful for:",
        "1. Making documents accessible to visually impaired users",
        "2. Creating audio versions of written content for multitasking", 
        "3. Learning through auditory processing",
        "",
        "The conversion process preserves the original text content while",
        "removing formatting artifacts that could interfere with natural speech.",
    ]
    
    for line in sample_text:
        if line:  # Skip empty lines for spacing
            c.drawString(100, y_position, line)
        y_position -= 20
        
        # Start a new page if we're running out of space
        if y_position < 100:
            c.showPage()
            c.setFont("Helvetica", 12)
            y_position = height - 100
    
    c.save()
    return output_path

if __name__ == "__main__":
    pdf_path = create_sample_pdf()
    print(f"Sample PDF created: {pdf_path}")