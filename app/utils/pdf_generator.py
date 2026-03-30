"""
PDF generation utility for inspection reports.
"""
import os
from weasyprint import HTML, CSS
from flask import url_for, current_app
from app.models import Inspection

def generate_pdf(inspection_id):
    """Generate PDF for a given inspection ID."""
    from flask import render_template
    inspection = Inspection.query.get_or_404(inspection_id)
    
    # Render the HTML template for PDF
    html_string = render_template('pdf/inspection_pdf.html', inspection=inspection)
    
    # Define CSS for PDF (we can also use external CSS)
    css_string = """
    @page {
        size: A4;
        margin: 2cm;
        @bottom-center {
            content: "Page " counter(page) " of " counter(pages);
            font-size: 9pt;
            color: #666;
        }
    }
    body {
        font-family: "Helvetica", "Arial", sans-serif;
        line-height: 1.5;
        color: #333;
    }
    .header {
        text-align: center;
        margin-bottom: 2cm;
    }
    .header h1 {
        font-size: 24pt;
        margin: 0;
    }
    .header h2 {
        font-size: 18pt;
        margin: 0;
        color: #666;
    }
    .section {
        margin-bottom: 1.5cm;
    }
    .section h2 {
        font-size: 16pt;
        border-bottom: 1px solid #ccc;
        padding-bottom: 2px;
        margin-bottom: 0.5cm;
    }
    .two-column {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1cm;
    }
    .photo-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 0.5cm;
    }
    .photo-item {
        page-break-inside: avoid;
        margin-bottom: 0.5cm;
    }
    .photo-item img {
        max-width: 100%;
        height: auto;
        border: 1px solid #ddd;
    }
    .photo-caption {
        font-size: 9pt;
        margin-top: 2px;
    }
    .photo-action {
        font-size: 9pt;
        font-weight: bold;
        margin-top: 2px;
    }
    .conclusion-status {
        font-size: 14pt;
        padding: 0.5cm;
        text-align: center;
        margin: 1cm 0;
    }
    .conclusion-status.ok {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .conclusion-status.minor {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
    .conclusion-status.major {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .footer {
        margin-top: 2cm;
        text-align: center;
        font-size: 9pt;
        color: #666;
    }
    """
    
    # Create HTML object
    html = HTML(string=html_string, base_url=current_app.config['WEASYPRINT_BASE_URL'])
    
    # Create CSS object
    css = CSS(string=css_string)
    
    # Generate PDF
    pdf_bytes = html.write_pdf(stylesheets=[css])
    
    return pdf_bytes