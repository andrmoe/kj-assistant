import json
import os
from typing import Any, Callable, Generator, Annotated
import requests
from pydantic import BaseModel, ValidationError, Field
from dotenv import load_dotenv
from typing_extensions import final

from abbreviation import abbreviation
from command_data import CommandData, CommandSession, SessionManager
from prompts import command_session_to_prompt

@final
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


class StreamedData(BaseModel):
    class StreamedChoice(BaseModel):
        class StreamedDelta(BaseModel):
            content: str
            role: str | None = None
        delta: StreamedDelta
    choices: list[StreamedChoice] = Field(min_length=1)


key_name = "OPENROUTER_KEY"


def get_api_key() -> str:
    load_dotenv()
    try:
        key = os.getenv(key_name)
        if isinstance(key, str):
           return key
        else:
           raise EnvironmentError(f"Returned key is not a str. Got a {type(key)} instead.") 
    except:
        print("Failed to load OpenRouter API key")
        raise


class Assistant:
    initial_message: str
    session: CommandSession
    session_manager: SessionManager

    def __init__(self, session_manager: SessionManager, remote_url: str, session_id: int | None = None, 
        verbose: bool = False):
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
                data = line[len("data:") :].strip()
                if data == "[DONE]":
                    break
                event = StreamedData.model_validate(json.loads(data))  # TODO: Write tests 
                # TODO: handle exceptions. Write the exception to a log, skip the bad chunk, and notify the user after the response
                delta = event.choices[0].delta  # TODO: Handle multiple choices
                yield Chunk(delta.content, delta.role)
    

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
