import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Generator

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
    token_generator: Generator[str, None, None],
) -> Generator[str, None, None]:
    for token in token_generator:
        yield f"data: {json.dumps(create_chunk(token, False))}"
    yield f"data: {json.dumps(create_chunk('', True))}"
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
    yield f"data: {json.dumps(last_chunk)}"


class StreamingHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()

        for word in LOREM_WORDS:
            chunk = (word + " ").encode("utf-8")
            self.wfile.write(f"{len(chunk):X}\r\n".encode("ascii"))
            self.wfile.write(chunk)
            self.wfile.write(b"\r\n")
            self.wfile.flush()

        self.wfile.write(b"0\r\n\r\n")
        self.wfile.flush()

    def log_message(self, format: str, *args: tuple[Any, ...]) -> None:
        return


@pytest.fixture
def streaming_server() -> Generator[str, None, None]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), StreamingHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield ""

    server.shutdown()
    server.server_close()
    thread.join()
