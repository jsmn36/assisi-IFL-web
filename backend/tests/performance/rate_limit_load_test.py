"""
Rate Limit Load Test
Test rate limiting under load
"""
import asyncio
import aiohttp
import time
from typing import List, Dict


class RateLimitLoadTester:
    """Load tester specifically for rate limits"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    async def test_rate_limit_enforcement(self, endpoint: str, limit: int):
        """Test that rate limit is properly enforced"""
        print(f"\n🧪 Testing rate limit enforcement on {endpoint}")
        print(f"   Expected limit: {limit}")

        async with aiohttp.ClientSession() as session:
            tasks = []
            num_requests = limit + 10
            for i in range(num_requests):
                tasks.append(self._make_request(session, endpoint))
            results = await asyncio.gather(*tasks)

        successful = sum(1 for r in results if r["status"] == 200)
        rate_limited = sum(1 for r in results if r["status"] == 429)

        print(f"   Successful: {successful}")
        print(f"   Rate limited: {rate_limited}")
        print(f"   Total: {len(results)}")

        if successful <= limit:
            print(f"   ✅ Rate limit properly enforced")
        else:
            print(f"   ❌ Rate limit not enforced (allowed {successful} > {limit})")

        return {
            "endpoint": endpoint,
            "expected_limit": limit,
            "successful": successful,
            "rate_limited": rate_limited,
            "properly_enforced": successful <= limit,
        }

    async def test_burst_handling(self, endpoint: str, burst_size: int):
        """Test handling of burst traffic"""
        print(f"\n🧪 Testing burst handling on {endpoint}")
        print(f"   Burst size: {burst_size}")

        async with aiohttp.ClientSession() as session:
            start = time.time()
            tasks = [self._make_request(session, endpoint) for _ in range(burst_size)]
            results = await asyncio.gather(*tasks)
            duration = time.time() - start

        successful = sum(1 for r in results if r["status"] == 200)
        rate_limited = sum(1 for r in results if r["status"] == 429)

        print(f"   Duration: {duration:.2f}s")
        print(f"   Successful: {successful}")
        print(f"   Rate limited: {rate_limited}")
        print(f"   Requests/sec: {burst_size/duration:.1f}")

        return {
            "burst_size": burst_size,
            "duration": duration,
            "successful": successful,
            "rate_limited": rate_limited,
            "requests_per_second": burst_size / duration,
        }

    async def _make_request(
        self, session: aiohttp.ClientSession, endpoint: str
    ) -> Dict:
        """Make single request"""
        try:
            url = f"{self.base_url}{endpoint}"
            async with session.get(url) as response:
                return {
                    "status": response.status,
                    "success": 200 <= response.status < 300,
                }
        except Exception as e:
            return {"status": 0, "success": False, "error": str(e)}


async def main():
    """Run rate limit load tests"""
    tester = RateLimitLoadTester()
    await tester.test_rate_limit_enforcement("/api/v1/health", 60)
    await tester.test_burst_handling("/api/v1/health", 100)


if __name__ == "__main__":
    print("🚀 Starting Rate Limit Load Tests...")
    asyncio.run(main())
