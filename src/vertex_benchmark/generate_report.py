import os
import json
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from vertex_benchmark.config import REGION_TO_CITY
from vertex_benchmark.database_utils import get_latest_batch_id, get_results_by_batch_id, get_db_connection
from vertex_benchmark.report_utils import compute_stats


# stats helpers imported from report_utils


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


def generate_pdf_report(batch_id=None, output_pdf=None):
    """Generate PDF benchmark report from database with averaged values."""

    if batch_id is None:
        batch_id = get_latest_batch_id()
        if not batch_id:
            print("No benchmark data found in the database!")
            return

    raw_data = get_results_by_batch_id(batch_id)

    if not raw_data:
        print(f"No data found for batch ID: {batch_id}")
        return

    # Generate output filename if not provided
    if output_pdf is None:
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
        output_pdf = f"./results/benchmark-report-{timestamp}.pdf"

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_pdf) or ".", exist_ok=True)

    # Determine number of cycles from the data
    num_cycles = max(row['cycle_num'] for row in raw_data)

    # Fetch batch metadata (version, config snapshot, timings)
    batch_meta = {
        'app_version': None,
        'config': None,
        'started_at': None,
        'ended_at': None,
    }
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT app_version, config_json, started_at, ended_at FROM batches WHERE batch_id=?", (batch_id,))
            row = cur.fetchone()
            if row:
                batch_meta['app_version'] = row['app_version']
                batch_meta['started_at'] = row['started_at']
                batch_meta['ended_at'] = row['ended_at']
                try:
                    batch_meta['config'] = json.loads(row['config_json']) if row['config_json'] else None
                except Exception:
                    batch_meta['config'] = None
    except Exception:
        pass

    # Calculate averages per region across all cycles
    region_data = {}
    for row in raw_data:
        region = row['region']
        if region not in region_data:
            region_data[region] = {
                'pro_times': [],
                'flash_times': [],
                'garden_models': row['garden_models']
            }

        # Collect times (already floats or None from DB)
        if row['pro_time_ms'] is not None:
            region_data[region]['pro_times'].append(row['pro_time_ms'])
        if row['flash_time_ms'] is not None:
            region_data[region]['flash_times'].append(row['flash_time_ms'])

    # Create averaged data for PDF
    data = []
    for region, values in region_data.items():
        avg_pro = sum(values['pro_times']) / len(values['pro_times']) if values['pro_times'] else None
        avg_flash = sum(values['flash_times']) / len(values['flash_times']) if values['flash_times'] else None

        data.append({
            'region': region,
            'Pro': avg_pro,
            'Flash': avg_flash,
            'Garden Models': values['garden_models']
        })

    # Sort by region name for consistent ordering
    data.sort(key=lambda x: x['region'])

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
    elements.append(
        Paragraph(f"European Regions - Averaged Results - {datetime.now().strftime('%d %B %Y')}", subtitle_style))
    elements.append(Spacer(1, 0.2 * inch))

    # Calculate statistics
    pro_times = [row['Pro'] for row in data]
    flash_times = [row['Flash'] for row in data]

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
    row_statuses = []

    for i, row in enumerate(data):
        region = row['region']
        city_name = REGION_TO_CITY.get(region, region)
        pro = f"{row['Pro']:.2f}ms" if row['Pro'] is not None else "Not Available"
        flash = f"{row['Flash']:.2f}ms" if row['Flash'] is not None else "Not Available"

        # Status indicator
        if row['Pro'] is not None and row['Flash'] is not None:
            status = "✓ Full"
        elif row['Pro'] is None and row['Flash'] is None:
            status = "✗ None"
        else:
            status = "⚠ Partial"

        table_data.append([city_name, region, pro, flash, status])
        row_statuses.append(status)

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
        pro_time = row['Pro']
        flash_time = row['Flash']

        # Color for Pro column
        pro_color = get_performance_color(pro_time, pro_max, pro_min)
        table_style.append(('BACKGROUND', (2, i), (2, i), pro_color))

        # Color for Flash column
        flash_color = get_performance_color(flash_time, flash_max, flash_min)
        table_style.append(('BACKGROUND', (3, i), (3, i), flash_color))

        # Status column color (derive from exact status value)
        status_value = row_statuses[i - 1]
        if status_value == "✓ Full":
            status_color = colors.Color(0.8, 1, 0.8)
        elif status_value == "⚠ Partial":
            status_color = colors.Color(1, 1, 0.8)
        else:  # "✗ None"
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

    # Compute summary statistics for additional insights
    pro_stats = compute_stats(pro_times)
    flash_stats = compute_stats(flash_times)

    if flash_times_valid:
        min_flash_time = min(flash_times_valid)
        fastest_flash_data = next((row for row in data if row['Flash'] == min_flash_time), None)
        if fastest_flash_data:
            fastest_flash_region = REGION_TO_CITY.get(fastest_flash_data['region'], fastest_flash_data['region'])
        else:
            fastest_flash_region = "Unknown"

    if pro_times_valid:
        min_pro_time = min(pro_times_valid)
        fastest_pro_data = next((row for row in data if row['Pro'] == min_pro_time), None)
        if fastest_pro_data:
            fastest_pro_region = REGION_TO_CITY.get(fastest_pro_data['region'], fastest_pro_data['region'])
        else:
            fastest_pro_region = "Unknown"

    ratio_insight = ""
    if pro_times_valid and flash_times_valid:
        pro_avg = sum(pro_times_valid) / len(pro_times_valid)
        flash_avg = sum(flash_times_valid) / len(flash_times_valid)
        ratio_val = pro_avg / flash_avg if flash_avg else None
        if ratio_val is not None:
            ratio_insight = f"• <b>Flash is {ratio_val:.1f}x faster</b> than Pro on average"

    insights = [
        f"• <b>Fastest Gemini 2.5 Flash:</b> {fastest_flash_region} ({min_flash_time:.2f}ms)" if flash_times_valid else "",
        f"• <b>Fastest Gemini 2.5 Pro:</b> {fastest_pro_region} ({min_pro_time:.2f}ms)" if pro_times_valid else "",
        ratio_insight,
        f"• <b>{len(pro_times_valid)} out of {len(data)} regions</b> support Gemini 2.5 Pro",
        f"• <b>{len(flash_times_valid)} out of {len(data)} regions</b> support Gemini 2.5 Flash"
    ]

    # Append statistical insights for Pro and Flash
    if pro_stats:
        stdev_text = f"{pro_stats['stdev']:.2f}ms" if pro_stats['stdev'] is not None else "N/A"
        insights.append(
            f"• <b>Pro stats:</b> mean {pro_stats['mean']:.2f}ms; stdev {stdev_text}; "
            f"p10 {pro_stats['p10']:.2f}ms, p50 {pro_stats['p50']:.2f}ms, p90 {pro_stats['p90']:.2f}ms"
        )
    if flash_stats:
        stdev_text_f = f"{flash_stats['stdev']:.2f}ms" if flash_stats['stdev'] is not None else "N/A"
        insights.append(
            f"• <b>Flash stats:</b> mean {flash_stats['mean']:.2f}ms; stdev {stdev_text_f}; "
            f"p10 {flash_stats['p10']:.2f}ms, p50 {flash_stats['p50']:.2f}ms, p90 {flash_stats['p90']:.2f}ms"
        )

    # Top 3 regions per model by average latency
    pro_ranked = [row for row in data if row['Pro'] is not None]
    flash_ranked = [row for row in data if row['Flash'] is not None]
    pro_ranked.sort(key=lambda r: r['Pro'])
    flash_ranked.sort(key=lambda r: r['Flash'])

    if pro_ranked:
        top3_pro = pro_ranked[:3]
        top3_pro_text = ", ".join(
            f"{REGION_TO_CITY.get(r['region'], r['region'])} ({r['Pro']:.2f}ms)" for r in top3_pro
        )
        insights.append(f"• <b>Top 3 Pro regions:</b> {top3_pro_text}")

    if flash_ranked:
        top3_flash = flash_ranked[:3]
        top3_flash_text = ", ".join(
            f"{REGION_TO_CITY.get(r['region'], r['region'])} ({r['Flash']:.2f}ms)" for r in top3_flash
        )
        insights.append(f"• <b>Top 3 Flash regions:</b> {top3_flash_text}")

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
    elements.append(
        Paragraph(f"Performance measured as averaged end-to-end response time across {num_cycles} test prompts",
                  footer_style))

    # Batch metadata footer lines (conditional)
    meta_segments = []
    if batch_meta.get('app_version'):
        meta_segments.append(f"Version {batch_meta['app_version']}")
    if batch_meta.get('started_at'):
        meta_segments.append(f"Started {batch_meta['started_at']}")
    if batch_meta.get('ended_at'):
        meta_segments.append(f"Ended {batch_meta['ended_at']}")

    meta_line = f"Batch {batch_id}"
    if meta_segments:
        meta_line += " • " + " • ".join(meta_segments)
    elements.append(Paragraph(meta_line, footer_style))

    cfg = batch_meta.get('config')
    if cfg:
        try:
            parts = []
            regions = cfg.get('regions') or []
            prompts = cfg.get('test_prompts') or []
            if regions:
                parts.append(f"regions={len(regions)}")
            if prompts:
                parts.append(f"prompts={len(prompts)}")
            models = cfg.get('models') or {}
            pro_variants = len(models.get('Pro') or [])
            flash_variants = len(models.get('Flash') or [])
            if pro_variants or flash_variants:
                parts.append(f"models(Pro={pro_variants}, Flash={flash_variants})")
            min_delay = cfg.get('min_delay_seconds')
            max_delay = cfg.get('max_delay_seconds')
            if min_delay is not None and max_delay is not None:
                parts.append(f"delay={min_delay}-{max_delay}s")
            if parts:
                elements.append(Paragraph("Config: " + "; ".join(parts), footer_style))
        except Exception:
            pass

    # Build PDF
    doc.build(elements)
    print(f"✓ PDF generated: {output_pdf}")
    return output_pdf


if __name__ == "__main__":
    import sys

    print(f"Generating PDF from latest benchmark data...")
    pdf_file = generate_pdf_report()
    if pdf_file:
        print(f"✓ Done! PDF saved to: {pdf_file}")
    else:
        sys.exit(1)
