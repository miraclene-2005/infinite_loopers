import os
import uvicorn
from main import app

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    print("=" * 60)
    print("Starting Multi-Agent Industrial Crisis Command Backend")
    print(f"API Endpoint : http://localhost:{port}")
    print(f"Interactive Docs: http://localhost:{port}/docs")
    print("=" * 60)
    uvicorn.run("main:app", host=host, port=port, reload=False)
