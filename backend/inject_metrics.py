import sys

with open("app/main.py", "r") as f:
    content = f.read()

metrics_code = """
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

"""

if "def metrics():" not in content:
    content = content.replace(
        'if __name__ == "__main__":', metrics_code + 'if __name__ == "__main__":'
    )
    with open("app/main.py", "w") as f:
        f.write(content)
    print("Metrics injected")
else:
    print("Metrics already injected")
