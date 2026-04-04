import fastapi
import uvicorn
import os

print('docker works')
print(os.environ.get("ANTHROPIC_API_KEY"))