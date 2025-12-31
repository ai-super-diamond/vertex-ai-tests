import sqlite3
from vertex_benchmark.database_utils import DB_FILE

def check_all_batches():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all batches with their region counts
    cursor.execute("""
        SELECT b.batch_id, b.started_at, COUNT(DISTINCT br.region) as region_count, COUNT(br.id) as total_records
        FROM batches b
        LEFT JOIN benchmark_results br ON b.batch_id = br.batch_id
        GROUP BY b.batch_id, b.started_at
        ORDER BY b.started_at DESC
    """)
    batches = cursor.fetchall()
    
    print("All batches in database:")
    print("-" * 80)
    for batch in batches:
        print(f"Batch ID: {batch['batch_id']}")
        print(f"  Started: {batch['started_at']}")
        print(f"  Regions: {batch['region_count']}")
        print(f"  Records: {batch['total_records']}")
        print()
    
    conn.close()

if __name__ == "__main__":
    check_all_batches()