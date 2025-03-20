import time
import asyncio
import aiohttp
import argparse
import statistics
import json
from datetime import datetime

class APIStressTest:
    def __init__(self, url, method='GET', data=None, headers=None, 
                 num_requests=100, concurrency=10, timeout=30):
        self.url = url
        self.method = method.upper()
        self.data = data
        self.headers = headers or {}
        self.num_requests = num_requests
        self.concurrency = concurrency
        self.timeout = timeout
        self.results = []
        self.failed_requests = 0
        self.successful_requests = 0

    async def make_request(self, session, request_id):
        start_time = time.perf_counter()
        try:
            if self.method == 'GET':
                async with session.get(self.url, headers=self.headers, timeout=self.timeout) as response:
                    await response.text()
                    status = response.status
            elif self.method == 'POST':
                async with session.post(self.url, json=self.data, headers=self.headers, timeout=self.timeout) as response:
                    await response.text()
                    status = response.status
            elif self.method == 'PUT':
                async with session.put(self.url, json=self.data, headers=self.headers, timeout=self.timeout) as response:
                    await response.text()
                    status = response.status
            elif self.method == 'DELETE':
                async with session.delete(self.url, headers=self.headers, timeout=self.timeout) as response:
                    await response.text()
                    status = response.status
            else:
                print(f"Unsupported method: {self.method}")
                return

            end_time = time.perf_counter()
            elapsed = end_time - start_time
            self.results.append(elapsed)

            if 200 <= status < 300:
                self.successful_requests += 1
            else:
                self.failed_requests += 1

            print(f"Request {request_id}: {status} in {elapsed:.2f}s")
            
        except Exception as e:
            end_time = time.perf_counter()
            elapsed = end_time - start_time
            self.failed_requests += 1
            print(f"Request {request_id}: Failed in {elapsed:.2f}s - {str(e)}")

    async def run(self):
        print(f"\nStarting stress test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"URL: {self.url}")
        print(f"Method: {self.method}")
        print(f"Requests: {self.num_requests}")
        print(f"Concurrency: {self.concurrency}")
        print(f"Timeout: {self.timeout}s")
        print("-" * 50)

        connector = aiohttp.TCPConnector(limit=self.concurrency)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            for i in range(1, self.num_requests + 1):
                tasks.append(self.make_request(session, i))

            # Run tasks in batches based on concurrency
            for i in range(0, len(tasks), self.concurrency):
                batch = tasks[i:i+self.concurrency]
                await asyncio.gather(*batch)

        self.show_results()

    def show_results(self):
        if not self.results:
            print("No successful requests to analyze.")
            return

        print("\n" + "=" * 50)
        print("TEST RESULTS")
        print("=" * 50)
        print(f"Total Requests: {self.num_requests}")
        print(f"Successful: {self.successful_requests}")
        print(f"Failed: {self.failed_requests}")
        print(f"Success Rate: {(self.successful_requests / self.num_requests * 100):.2f}%")

        # Calculate statistics
        total_time = sum(self.results)
        avg_time = statistics.mean(self.results)
        min_time = min(self.results)
        max_time = max(self.results)
        median_time = statistics.median(self.results)

        try:
            p95 = sorted(self.results)[int(len(self.results) * 0.95)]
            p99 = sorted(self.results)[int(len(self.results) * 0.99)]
        except IndexError:
            p95 = "N/A"
            p99 = "N/A"

        # FIXME
        requests_per_second = self.successful_requests / total_time

        print("\nResponse Time (seconds):")
        print(f"  Avg: {avg_time:.3f}")
        print(f"  Min: {min_time:.3f}")
        print(f"  Max: {max_time:.3f}")
        print(f"  Median: {median_time:.3f}")
        print(f"  95th Percentile: {p95 if isinstance(p95, str) else p95:.3f}")
        print(f"  99th Percentile: {p99 if isinstance(p99, str) else p99:.3f}")
        print(f"\nRequests Per Second: {requests_per_second:.2f}")

def main():
    parser = argparse.ArgumentParser(description='API Endpoint Stress Tester')
    parser.add_argument('url', help='API endpoint URL to test')
    parser.add_argument('-m', '--method', default='GET', help='HTTP method (GET, POST, PUT, DELETE)')
    parser.add_argument('-d', '--data', help='JSON data for POST/PUT requests')
    parser.add_argument('-H', '--header', action='append', help='Headers in format "Key: Value"')
    parser.add_argument('-n', '--num-requests', type=int, default=128, help='Number of requests to make')
    parser.add_argument('-c', '--concurrency', type=int, default=32, help='Concurrent requests')
    parser.add_argument('-t', '--timeout', type=int, default=30, help='Request timeout in seconds')

    args = parser.parse_args()

    # Process headers
    headers = {}
    if args.header:
        for header in args.header:
            try:
                key, value = header.split(':', 1)
                headers[key.strip()] = value.strip()
            except ValueError:
                print(f"Invalid header format: {header}. Use 'Key: Value'")

    # Process data for POST/PUT
    data = None
    if args.data:
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError:
            print(f"Invalid JSON data: {args.data}")
            return

    stress_test = APIStressTest(
        url=args.url,
        method=args.method,
        data=data,
        headers=headers,
        num_requests=args.num_requests,
        concurrency=args.concurrency,
        timeout=args.timeout
    )
    
    asyncio.run(stress_test.run())

if __name__ == "__main__":
    main()
