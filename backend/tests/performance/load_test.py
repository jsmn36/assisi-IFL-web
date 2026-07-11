import asyncio
import aiohttp
import time
from typing import List, Dict
import statistics


class LoadTester:
    """Simple load testing utility"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[Dict] = []

    async def make_request(
        self, session: aiohttp.ClientSession, endpoint: str, method: str = "GET"
    ) -> Dict:
        """Make single request and measure time"""

        start = time.perf_counter()

        try:
            url = f"{self.base_url}{endpoint}"
            async with session.request(method, url) as response:
                status = response.status
                await response.text()
                duration = time.perf_counter() - start

                return {
                    "endpoint": endpoint,
                    "status": status,
                    "duration": duration,
                    "success": 200 <= status < 300,
                }

        except Exception as e:
            return {
                "endpoint": endpoint,
                "status": 0,
                "duration": time.perf_counter() - start,
                "success": False,
                "error": str(e),
            }

    async def run_concurrent_requests(
        self, endpoint: str, num_requests: int = 100, method: str = "GET"
    ) -> Dict:
        """Run concurrent requests"""

        print(f"\n🔥 Load Testing: {num_requests} concurrent requests to {endpoint}")

        async with aiohttp.ClientSession() as session:
            tasks = [
                self.make_request(session, endpoint, method)
                for _ in range(num_requests)
            ]

            start = time.perf_counter()
            results = await asyncio.gather(*tasks)
            total_time = time.perf_counter() - start

        # Analyze results
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        durations = [r["duration"] for r in successful]

        stats = {
            "endpoint": endpoint,
            "total_requests": num_requests,
            "successful": len(successful),
            "failed": len(failed),
            "total_time": total_time,
            "requests_per_second": num_requests / total_time if total_time > 0 else 0,
            "avg_response_time": statistics.mean(durations) if durations else 0,
            "min_response_time": min(durations) if durations else 0,
            "max_response_time": max(durations) if durations else 0,
            "median_response_time": statistics.median(durations) if durations else 0,
        }

        # Print results
        print(f"✅ Successful: {stats['successful']}/{num_requests}")
        print(f"❌ Failed: {stats['failed']}")
        print(f"⚡ Requests/sec: {stats['requests_per_second']:.2f}")
        print(f"⏱️ Avg response: {stats['avg_response_time']*1000:.2f} ms")
        print(f"⏱️ Min response: {stats['min_response_time']*1000:.2f} ms")
        print(f"⏱️ Max response: {stats['max_response_time']*1000:.2f} ms")
        print(f"⏱️ Median: {stats['median_response_time']*1000:.2f} ms")

        return stats

    async def run_sustained_load(
        self, endpoint: str, duration_seconds: int = 60, requests_per_second: int = 10
    ):
        """Run sustained load test"""

        print(
            f"\n🔥 Sustained Load: {requests_per_second} req/sec for {duration_seconds}s"
        )

        start_time = time.perf_counter()
        interval = 1.0 / requests_per_second

        async with aiohttp.ClientSession() as session:
            while time.perf_counter() - start_time < duration_seconds:
                await self.make_request(session, endpoint)
                await asyncio.sleep(interval)

        print("✅ Sustained load test completed")


async def main():
    """Run load tests"""

    tester = LoadTester()

    # Test endpoints
    endpoints = [
        "/api/v1/health",
        "/api/v1/cached/cache/stats",
    ]

    for endpoint in endpoints:
        await tester.run_concurrent_requests(endpoint, num_requests=50)
        await asyncio.sleep(2)

    # Optional sustained test
    # await tester.run_sustained_load("/api/v1/health", duration_seconds=30, requests_per_second=10)


if __name__ == "__main__":
    print("🚀 Starting Load Tests...")
    asyncio.run(main())
