import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Generator, Iterable

import pytest

LOREM_WORDS = (
    "Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod "
    "tempor incididunt ut labore et dolore magna aliqua"
).split()


def create_chunk(content: str, is_finished: bool) -> dict[str, Any]:
    data = {
        "id": "gen-1782756883-HgZzVRY6zw9Z4CQD6FnN",
        "object": "chat.completion.chunk",
        "created": 1782756883,
        "model": "mock_model",
        "provider": "kj-assistant",
        "choices": [
            {
                "index": 0,
                "delta": {"content": content, "role": "assistant"},
                "finish_reason": "stop" if is_finished else None,
                "native_finish_reason": "completed" if is_finished else None,
            }
        ],
    }
    return data


def create_chunks(
    token_generator: Iterable[str],
) -> Generator[str, None, None]:
    for token in token_generator:
        yield f"data: {json.dumps(create_chunk(token, False))}\n\n"
    yield f"data: {json.dumps(create_chunk('', True))}\n\n"
    last_chunk = create_chunk("", True)
    last_chunk["usage"] = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "cost": 0.0,
        "is_byok": False,
        "prompt_tokens_details": {
            "cached_tokens": 0,
            "cache_write_tokens": 0,
            "audio_tokens": 0,
            "video_tokens": 0,
        },
        "cost_details": {
            "upstream_inference_cost": 0.0,
            "upstream_inference_prompt_cost": 0.0,
            "upstream_inference_completions_cost": 0.0,
        },
        "completion_tokens_details": {
            "reasoning_tokens": 0,
            "image_tokens": 0,
            "audio_tokens": 0,
        },
    }
    yield f"data: {json.dumps(last_chunk)}\n\n"
    yield "data: [DONE]\n\n"


class StreamingHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        if self.path == "/no_reply":
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()
            return
        for chunk in create_chunks(LOREM_WORDS):
            self.wfile.write(f"{len(chunk):X}\r\n".encode("ascii"))
            self.wfile.write(chunk.encode("utf-8"))
            self.wfile.write(b"\r\n")
            self.wfile.flush()

        self.wfile.write(b"0\r\n\r\n")
        self.wfile.flush()

    def log_message(self, format: str, *args: tuple[Any, ...]) -> None:
        return


@pytest.fixture
def mock_ai_api() -> Generator[None, None, None]:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), StreamingHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield None

    server.shutdown()
    server.server_close()
    thread.join()
