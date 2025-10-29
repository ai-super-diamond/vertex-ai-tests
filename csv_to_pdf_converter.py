import csv
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

# Region to City Name Mapping
REGION_TO_CITY = {
    "europe-west1": "Belgium (Brussels)",
    "europe-west2": "United Kingdom (London)",
    "europe-west3": "Germany (Frankfurt)",
    "europe-west4": "Netherlands (Amsterdam)",
    "europe-west6": "Switzerland (Zurich)",
    "europe-west8": "Italy (Milan)",
    "europe-west9": "France (Paris)",
    "europe-north1": "Finland (Helsinki)",
    "europe-central2": "Poland (Warsaw)",
    "europe-southwest1": "Spain (Madrid)"
}


def parse_time(time_str):
    """Convert time string like '1234.56ms' to float, or None if not available"""
    if time_str == "Not Available" or time_str == "N/A":
        return None
    try:
        return float(time_str.replace("ms", ""))
    except:
        return None


def get_performance_color(value, max_val, min_val):
    """Get color based on performance (green for fast, red for slow)"""
    if value is None:
        return colors.lightgrey

    # Normalize value between 0 and 1
    if max_val == min_val:
        normalized = 0.5
    else:
        normalized = (value - min_val) / (max_val - min_val)

    # Green for fast (low values), Red for slow (high values)
    if normalized < 0.33:
        return colors.Color(0.8, 1, 0.8)  # Light green
    elif normalized < 0.67:
        return colors.Color(1, 1, 0.8)  # Light yellow
    else:
        return colors.Color(1, 0.9, 0.9)  # Light red


def convert_csv_to_pdf(csv_file, output_pdf=None):
    """Convert CSV benchmark results to elegant PDF"""

    # Generate output filename if not provided
    if output_pdf is None:
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
        output_pdf = f"./results/benchmark-report-{timestamp}.pdf"

    # Read CSV data
    data = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Filter out US regions
            if not row['region'].startswith('us-'):
                data.append(row)

    if not data:
        print("No European data found in CSV!")
        return

    # Create PDF
    doc = SimpleDocTemplate(output_pdf, pagesize=A4,
                            topMargin=0.5 * inch, bottomMargin=0.5 * inch,
                            leftMargin=0.5 * inch, rightMargin=0.5 * inch)

    # Container for PDF elements
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a73e8'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.grey,
        spaceAfter=20,
        alignment=TA_CENTER
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1a73e8'),
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )

    # Title
    elements.append(Paragraph("Vertex AI Gemini 2.5 Performance Benchmark", title_style))
    elements.append(Paragraph(f"European Regions - {datetime.now().strftime('%d %B %Y')}", subtitle_style))
    elements.append(Spacer(1, 0.2 * inch))

    # Calculate statistics
    pro_times = [parse_time(row['Pro']) for row in data]
    flash_times = [parse_time(row['Flash']) for row in data]

    pro_times_valid = [t for t in pro_times if t is not None]
    flash_times_valid = [t for t in flash_times if t is not None]

    # Summary Statistics
    elements.append(Paragraph("Executive Summary", heading_style))

    summary_data = [
        ['Metric', 'Gemini 2.5 Pro', 'Gemini 2.5 Flash'],
        ['Regions Tested', str(len(data)), str(len(data))],
        ['Available In', f"{len(pro_times_valid)} regions", f"{len(flash_times_valid)} regions"],
        ['Fastest Response',
         f"{min(pro_times_valid):.2f}ms" if pro_times_valid else "N/A",
         f"{min(flash_times_valid):.2f}ms" if flash_times_valid else "N/A"],
        ['Average Response',
         f"{sum(pro_times_valid) / len(pro_times_valid):.2f}ms" if pro_times_valid else "N/A",
         f"{sum(flash_times_valid) / len(flash_times_valid):.2f}ms" if flash_times_valid else "N/A"],
        ['Slowest Response',
         f"{max(pro_times_valid):.2f}ms" if pro_times_valid else "N/A",
         f"{max(flash_times_valid):.2f}ms" if flash_times_valid else "N/A"]
    ]

    summary_table = Table(summary_data, colWidths=[2.5 * inch, 2 * inch, 2 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)])
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 0.3 * inch))

    # Detailed Results
    elements.append(Paragraph("Detailed Regional Performance", heading_style))

    # Prepare table data with city names and region codes
    table_data = [['Location', 'Region Code', 'Gemini 2.5 Pro', 'Gemini 2.5 Flash', 'Status']]

    for i, row in enumerate(data):
        region = row['region']
        city_name = REGION_TO_CITY.get(region, region)
        pro = row['Pro']
        flash = row['Flash']

        # Status indicator
        if pro != "Not Available" and flash != "Not Available":
            status = "✓ Full"
        elif pro == "Not Available" and flash == "Not Available":
            status = "✗ None"
        else:
            status = "⚠ Partial"

        table_data.append([city_name, region, pro, flash, status])

    # Create table
    results_table = Table(table_data, colWidths=[2 * inch, 1.5 * inch, 1.2 * inch, 1.2 * inch, 0.8 * inch])

    # Calculate colors for cells
    pro_max = max(pro_times_valid) if pro_times_valid else 0
    pro_min = min(pro_times_valid) if pro_times_valid else 0
    flash_max = max(flash_times_valid) if flash_times_valid else 0
    flash_min = min(flash_times_valid) if flash_times_valid else 0

    # Base table style
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('FONTNAME', (1, 1), (1, -1), 'Courier'),
        ('FONTSIZE', (1, 1), (1, -1), 7),
        ('TEXTCOLOR', (1, 1), (1, -1), colors.grey),
    ]

    # Add color coding based on performance
    for i, row in enumerate(data, start=1):
        pro_time = parse_time(row['Pro'])
        flash_time = parse_time(row['Flash'])

        # Color for Pro column
        pro_color = get_performance_color(pro_time, pro_max, pro_min)
        table_style.append(('BACKGROUND', (2, i), (2, i), pro_color))

        # Color for Flash column
        flash_color = get_performance_color(flash_time, flash_max, flash_min)
        table_style.append(('BACKGROUND', (3, i), (3, i), flash_color))

        # Status column color
        status_color = colors.Color(0.8, 1, 0.8) if "Full" in table_data[i][4] else colors.Color(1, 0.95, 0.8)
        if "None" in table_data[i][4]:
            status_color = colors.Color(1, 0.9, 0.9)
        table_style.append(('BACKGROUND', (4, i), (4, i), status_color))

    results_table.setStyle(TableStyle(table_style))
    elements.append(results_table)

    # Add legend
    elements.append(Spacer(1, 0.2 * inch))
    legend_style = ParagraphStyle(
        'Legend',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_LEFT
    )
    elements.append(Paragraph("Color Legend: <font color='green'>■</font> Fastest 33% | "
                              "<font color='orange'>■</font> Middle 33% | "
                              "<font color='red'>■</font> Slowest 33%", legend_style))

    # Key Insights
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph("Key Insights", heading_style))

    if flash_times_valid:
        fastest_flash_idx = flash_times.index(min(flash_times_valid))
        fastest_flash_region = REGION_TO_CITY.get(data[fastest_flash_idx]['region'], data[fastest_flash_idx]['region'])

    if pro_times_valid:
        fastest_pro_idx = pro_times.index(min(pro_times_valid))
        fastest_pro_region = REGION_TO_CITY.get(data[fastest_pro_idx]['region'], data[fastest_pro_idx]['region'])

    insights = [
        f"• <b>Fastest Gemini 2.5 Flash:</b> {fastest_flash_region} ({min(flash_times_valid):.2f}ms)" if flash_times_valid else "",
        f"• <b>Fastest Gemini 2.5 Pro:</b> {fastest_pro_region} ({min(pro_times_valid):.2f}ms)" if pro_times_valid else "",
        f"• <b>Flash is {sum(pro_times_valid) / len(pro_times_valid) / sum(flash_times_valid) * len(flash_times_valid):.1f}x faster</b> than Pro on average" if pro_times_valid and flash_times_valid else "",
        f"• <b>{len(pro_times_valid)} out of {len(data)} regions</b> support Gemini 2.5 Pro",
        f"• <b>{len(flash_times_valid)} out of {len(data)} regions</b> support Gemini 2.5 Flash"
    ]

    for insight in insights:
        if insight:
            elements.append(Paragraph(insight, styles['Normal']))
            elements.append(Spacer(1, 0.1 * inch))

    # Footer
    elements.append(Spacer(1, 0.3 * inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    elements.append(Paragraph(f"Generated on {datetime.now().strftime('%d %B %Y at %H:%M')}", footer_style))
    elements.append(Paragraph("Performance measured as end-to-end response time for simple prompt", footer_style))

    # Build PDF
    doc.build(elements)
    print(f"✓ PDF generated: {output_pdf}")
    return output_pdf


if __name__ == "__main__":
    import sys

    # Get the latest CSV file from results directory
    results_dir = "./results"
    csv_files = [f for f in os.listdir(results_dir) if f.endswith('.csv')]

    if not csv_files:
        print("No CSV files found in results directory!")
        sys.exit(1)

    # Sort by modification time and get the latest
    csv_files.sort(key=lambda x: os.path.getmtime(os.path.join(results_dir, x)), reverse=True)
    latest_csv = os.path.join(results_dir, csv_files[0])

    print(f"Converting {latest_csv} to PDF...")
    pdf_file = convert_csv_to_pdf(latest_csv)
    print(f"✓ Done! PDF saved to: {pdf_file}")
