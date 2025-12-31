import sys
from vertex_benchmark.generate_report import generate_pdf_report

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_pdf_for_batch.py <batch_id>")
        print("Available batch IDs with 10 regions:")
        print("  49694cdc-611a-4573-8ce7-9e6068db6475")
        print("  c726b858-302d-4ff5-bd32-e0a82c8d8383")
        print("  26d19cae-0604-42ae-bd97-373e25b80b65")
        return
    
    batch_id = sys.argv[1]
    print(f"Generating PDF for batch ID: {batch_id}")
    
    try:
        pdf_file = generate_pdf_report(batch_id=batch_id)
        if pdf_file:
            print(f"✓ PDF generated successfully: {pdf_file}")
        else:
            print("✗ Failed to generate PDF")
    except Exception as e:
        print(f"✗ Error generating PDF: {e}")

if __name__ == "__main__":
    main()