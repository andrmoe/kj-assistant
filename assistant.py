import json
from typing import Any, Callable, Generator

import requests

from abbreviation import abbreviation
from cli import default_storage_path
from command_data import CommandData, CommandSession, SessionManager
from prompts import command_session_to_prompt


class Chunk:
    def __init__(
        self,
        content: str,
        role: str | None = None,
        context: list[int] | None = None,
    ):
        self.content = content
        self.role = role
        self.context = context


def get_api_key() -> str:
    try:
        key = json.loads(
            (default_storage_path() / ".env").read_text(encoding="utf-8")
        )["openrouter"]
        if isinstance(key, str):
           return key
        else:
           raise EnvironmentError(f"Returned key is not a str. Got a {type(key)} instead.") 
    except:
        print("Failed to load OpenRouter API key")
        raise
"https://openrouter.ai/api/v1/chat/completions"

class Assistant:
    initial_message: str
    session: CommandSession
    session_manager: SessionManager
    ai_api: Callable[[str], Generator[Chunk, None, None]]

    def __init__(self, session_manager: SessionManager, session_id: int | None = None, 
                 verbose: bool = False, remote_url: str = "http://127.0.0.1:8000"):
        self.verbose = verbose
        self.remote_url = remote_url
        self.session_manager = session_manager
        self.initial_message = ""
        self.model = "openai/gpt-5.2"
        if session_id is None:
            s = self.session_manager.load_most_recent_session()
        else:
            s = self.session_manager.load(session_id)
            # Passing a session id indicates that the user switched sessions.
            # They should therefore see the last message from that session.
            if s.commands:
                self.initial_message = s.commands[
                    -1
                ].ai_response  # TODO: Truncate this and make it prettier.
        self.session = s


    def query_remote_ai(self, prompt: str) -> Generator[Chunk, None, None]:
        headers = {"Authorization": f"Bearer {get_api_key()}"}
        request_data = {
            "model": self.model,
            "messages": [{"role": "system", "content": prompt}],
            "stream": True,
        }
    
        response = requests.post(self.remote_url, headers=headers, json=request_data, stream=True)
        response.raise_for_status()
        response.encoding = "utf-8"
        
        for line in response.iter_lines(decode_unicode=True):
            if line and not line.startswith(":") and line.startswith("data:"):
                data: str = line[len("data:") :].strip()
                if data == "[DONE]":
                    break
                event: dict[str, Any] = json.loads(data)
                if "choices" not in event:
                    raise IOError("'choices' not present in response from openrouter")
                choices: list[dict[str, Any]] = event["choices"]
                if len(choices) == 0:
                    raise IOError("'choices' from openrouter is empty")
                choice: dict[str, Any] = choices[0]  # TODO: Handle multiple choices
                if "delta" not in choice:
                    raise IOError("No 'delta' in response from openrouter")
                delta: dict[str, Any] = choice["delta"]
                if "content" not in delta or not isinstance(delta["content"], str):
                    raise IOError("No 'content' in response from openrouter")
                role: str | None = delta["role"] if "role" in delta else None
                yield Chunk(delta["content"], role)
    

    def new_command(
        self, command: CommandData, give_ai_response: bool = True
    ) -> Generator[str, None, None]:
        self.session.commands.append(command)
        prompt = command_session_to_prompt(self.session)
        if self.verbose:
            yield f"Prompt to {abbreviation}:\n{prompt}\n"
        if give_ai_response:
            for chunk in self.query_remote_ai(prompt):
                command.ai_response += chunk.content
                yield chunk.content
        self.session.save()
