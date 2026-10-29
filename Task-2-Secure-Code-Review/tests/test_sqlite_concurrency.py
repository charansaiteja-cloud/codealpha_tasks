import concurrent.futures
import sqlite3


def worker_query(db_path):
    # Test connection with check_same_thread=False under concurrent load
    conn = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    res = cursor.fetchone()
    conn.close()
    return res[0]


def test_concurrent_sqlite_requests(tmp_path):
    db_path = str(tmp_path / "test.db")

    # Initialize test DB
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE IF NOT EXISTS test (id INT)")
    conn.commit()
    conn.close()

    # Run 20 concurrent threads querying the SQLite DB
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker_query, db_path) for _ in range(20)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert all(r == 1 for r in results)
