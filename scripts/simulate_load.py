import boto3
import time
import uuid
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

class CopyStats:
    def __init__(self):
        self.total_copies = 0
        self.lock = Lock()
    
    def increment(self):
        with self.lock:
            self.total_copies += 1
    
    def get_total(self):
        with self.lock:
            return self.total_copies

def copy_file(s3_client, source_bucket, source_key, dest_bucket, dest_prefix, stats):
    try:
        new_key = f"{dest_prefix}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())}"
        s3_client.copy_object(
            Bucket=dest_bucket,
            Key=new_key,
            CopySource={'Bucket': source_bucket, 'Key': source_key}
        )
        stats.increment()
        return True
    except Exception as e:
        print(f"Error copying file: {e}")
        return False

def log_progress(stats, start_time):
    while True:
        total = stats.get_total()
        elapsed = time.time() - start_time
        rate = total / (elapsed / 60) if elapsed > 0 else 0
        print(f"Files copied: {total}, Current rate: {rate:.1f} files/minute")
        time.sleep(10)

def stress_test(source_bucket, source_key, dest_bucket, dest_prefix='', copies_per_minute=5000, duration_minutes=1):
    s3_client = boto3.client('s3')
    max_workers = min(copies_per_minute, 200)
    stats = CopyStats()
    
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    # Start logging thread
    import threading
    log_thread = threading.Thread(target=log_progress, args=(stats, start_time), daemon=True)
    log_thread.start()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        while time.time() < end_time:
            batch_start = time.time()
            futures = []
            
            for _ in range(int(copies_per_minute / 60)):
                futures.append(executor.submit(
                    copy_file, s3_client, source_bucket, source_key, dest_bucket, dest_prefix, stats
                ))
            
            completed = sum(1 for f in futures if f.result())
            
            elapsed = time.time() - batch_start
            if elapsed < 1:
                time.sleep(1 - elapsed)
    
    final_total = stats.get_total()
    total_time = time.time() - start_time
    print(f"\nTest complete. Copied {final_total} files in {total_time:.1f} seconds")
    print(f"Average rate: {final_total / (total_time / 60):.1f} files/minute")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='S3 Copy Stress Test')
    parser.add_argument('-s', '--source-bucket', required=True, help='Source bucket name')
    parser.add_argument('-k', '--source-key', required=True, help='Source file key')
    parser.add_argument('-d', '--dest-bucket', required=True, help='Destination bucket name')
    parser.add_argument('-p', '--dest-prefix', default='', help='Destination prefix (folder)')
    parser.add_argument('-r', '--rate', type=int, default=5000, help='Copies per minute (default: 5000)')
    parser.add_argument('-t', '--duration', type=int, default=1, help='Duration in minutes')
    
    args = parser.parse_args()
    
    print(f"Starting stress test at {args.rate} copies per minute...")
    stress_test(
        args.source_bucket,
        args.source_key,
        args.dest_bucket,
        args.dest_prefix.strip('/'),
        args.rate,
        args.duration
    )