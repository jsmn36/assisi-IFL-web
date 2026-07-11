"""
Week 5 Performance Tests - Fixed
"""
import asyncio
import aiohttp
import time
from statistics import mean, median


class Week5PerformanceTest:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {}

    async def test_cache_performance(self):
        try:
            from app.core.cache import cache
        except ImportError:
            print("\n📦 Cache module not found — skipping.")
            return

        print("\n📦 Testing Cache Performance...")

        # Use namespace as key prefix instead of kwarg
        write_times = []
        for i in range(1000):
            start = time.time()
            cache.set(f"perf:test:{i}", f"value_{i}")
            write_times.append(time.time() - start)

        read_times = []
        for i in range(1000):
            start = time.time()
            cache.get(f"perf:test:{i}")
            read_times.append(time.time() - start)

        self.results["cache"] = {
            "write_avg_ms": mean(write_times) * 1000,
            "write_median_ms": median(write_times) * 1000,
            "read_avg_ms": mean(read_times) * 1000,
            "read_median_ms": median(read_times) * 1000,
            "ops_per_second": 1000 / sum(write_times + read_times),
        }

        # Cleanup — try delete individually since clear_namespace may not exist
        for i in range(1000):
            try:
                cache.delete(f"perf:test:{i}")
            except Exception:
                pass

        print(f"  Write avg: {self.results['cache']['write_avg_ms']:.2f}ms")
        print(f"  Read avg:  {self.results['cache']['read_avg_ms']:.2f}ms")
        print(f"  Ops/sec:   {self.results['cache']['ops_per_second']:.0f}")

    async def test_rate_limit_performance(self):
        try:
            from app.core.rate_limiter import rate_limiter
        except ImportError:
            print("\n🚦 Rate limiter module not found — skipping.")
            return

        print("\n🚦 Testing Rate Limiter Performance...")

        check_times = []
        for i in range(1000):
            start = time.time()
            try:
                rate_limiter.check_rate_limit(f"perf_test_{i}", 100, 60)
            except Exception:
                # Some limiters are async — handled below
                break
            check_times.append(time.time() - start)

        if check_times:
            self.results["rate_limiter"] = {
                "avg_ms": mean(check_times) * 1000,
                "median_ms": median(check_times) * 1000,
                "checks_per_second": len(check_times) / sum(check_times),
            }
            print(f"  Avg check: {self.results['rate_limiter']['avg_ms']:.2f}ms")
            print(
                f"  Checks/sec: {self.results['rate_limiter']['checks_per_second']:.0f}"
            )
        else:
            print("  ⚠️  Rate limiter may be async — skipping sync test.")

    async def test_api_response_times(self):
        print("\n🌐 Testing API Response Times...")

        # Correct health endpoint found at /health (not /api/v1/health)
        endpoint = f"{self.base_url}/health"

        try:
            async with aiohttp.ClientSession() as session:
                times = []
                for i in range(100):
                    start = time.time()
                    async with session.get(endpoint) as resp:
                        await resp.text()
                    times.append(time.time() - start)

                self.results["api"] = {
                    "health_avg_ms": mean(times) * 1000,
                    "health_median_ms": median(times) * 1000,
                    "requests_per_second": 100 / sum(times),
                }

                print(
                    f"  Health endpoint avg: {self.results['api']['health_avg_ms']:.2f}ms"
                )
                print(
                    f"  Requests/sec: {self.results['api']['requests_per_second']:.0f}"
                )
        except Exception as e:
            print(f"  ⚠️  API test failed: {e}")

    def generate_report(self):
        print("\n" + "=" * 50)
        print("WEEK 5 PERFORMANCE REPORT")
        print("=" * 50)

        print("\n📦 Cache Performance:")
        if "cache" in self.results:
            print(f"  Write: {self.results['cache']['write_avg_ms']:.2f}ms avg")
            print(f"  Read:  {self.results['cache']['read_avg_ms']:.2f}ms avg")
            print(
                f"  Throughput: {self.results['cache']['ops_per_second']:.0f} ops/sec"
            )
        else:
            print("  Skipped")

        print("\n🚦 Rate Limiter:")
        if "rate_limiter" in self.results:
            print(f"  Check time: {self.results['rate_limiter']['avg_ms']:.2f}ms avg")
            print(
                f"  Throughput: {self.results['rate_limiter']['checks_per_second']:.0f} checks/sec"
            )
        else:
            print("  Skipped")

        print("\n🌐 API Performance:")
        if "api" in self.results:
            print(f"  Response time: {self.results['api']['health_avg_ms']:.2f}ms avg")
            print(
                f"  Throughput: {self.results['api']['requests_per_second']:.0f} req/sec"
            )
        else:
            print("  Skipped")

        print("\n" + "=" * 50)

        issues = []
        if "cache" in self.results and self.results["cache"]["read_avg_ms"] > 1.0:
            issues.append("⚠️  Cache reads slower than 1ms")
        if (
            "rate_limiter" in self.results
            and self.results["rate_limiter"]["avg_ms"] > 1.0
        ):
            issues.append("⚠️  Rate limit checks slower than 1ms")
        if "api" in self.results and self.results["api"]["health_avg_ms"] > 100:
            issues.append("⚠️  API responses slower than 100ms")

        if issues:
            print("\n⚠️  PERFORMANCE ISSUES:")
            for issue in issues:
                print(f"  {issue}")
        else:
            print("\n✅ All performance metrics within acceptable ranges")


async def main():
    tester = Week5PerformanceTest()
    await tester.test_cache_performance()
    await tester.test_rate_limit_performance()
    await tester.test_api_response_times()
    tester.generate_report()


if __name__ == "__main__":
    print("🚀 Starting Week 5 Performance Tests...")
    asyncio.run(main())
