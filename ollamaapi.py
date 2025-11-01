import requests
import json
from typing import Generator, Any

def query_ollama(prompt: str, url: str = "http://localhost:11434/api/generate", 
                 model: str = "llama3.2-vision:latest") -> Generator[str | list[int], None, None]:
    
    headers = {"Content-Type": "application/json"}
    data = {"model": model, "prompt": prompt, "stream": True}

    response = requests.post(url, headers=headers, data=json.dumps(data), stream=True)
    session_context: list[int] | None = None
    if response.status_code == 200:
        for line in response.iter_lines():
            if line:
                chunk: dict[str, Any] = json.loads(line.decode("utf-8"))
                if "response" in chunk:
                    #print(chunk["response"], end="", flush=True)
                    yield chunk["response"]
                if "context" in chunk:
                    session_context = chunk["context"]
                if chunk.get("done", False):
                    break
        if session_context is not None:
            yield session_context
        return
    else:
        raise IOError(f"Error {response.status_code}: {response.text}")
