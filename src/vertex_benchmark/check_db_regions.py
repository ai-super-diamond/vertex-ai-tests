import sqlite3
from vertex_benchmark.database_utils import DB_FILE

def check_regions():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get distinct regions
    cursor.execute("SELECT DISTINCT region FROM benchmark_results")
    regions = cursor.fetchall()
    
    print(f"Found {len(regions)} distinct regions:")
    for region in regions:
        print(f"  - {region['region']}")
    
    # Get latest batch info
    cursor.execute("SELECT batch_id, COUNT(*) as count FROM benchmark_results GROUP BY batch_id ORDER BY batch_id DESC LIMIT 1")
    batch_info = cursor.fetchone()
    
    if batch_info:
        print(f"\nLatest batch {batch_info['batch_id']} has {batch_info['count']} records")
        
        # Get regions for latest batch
        cursor.execute("SELECT DISTINCT region FROM benchmark_results WHERE batch_id = ?", (batch_info['batch_id'],))
        batch_regions = cursor.fetchall()
        print(f"Regions in latest batch ({len(batch_regions)}):")
        for region in batch_regions:
            print(f"  - {region['region']}")
    else:
        print("No batch data found")
    
    conn.close()

if __name__ == "__main__":
    check_regions()