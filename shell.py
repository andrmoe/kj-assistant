import os
import sys
from pathlib import Path
from typing import Iterable, Optional, Sequence, Any
import argparse
import re

from command_data import CommandData, SessionManager
from assistant import Assistant
from abbreviation import abbreviation
from cli import get_arg_parser


def parse_command_history(history: str) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    for line in history.split('\n'):
        re_match = re.match(r"^(\d+)\ {2}(.*)$", line.strip())
        if re_match is None:
            raise EnvironmentError(f"Could not parse command history. There's either a bug in the parser, "
                                   f"or a weird bash shell. Unparsed line:\n{line}")
        result.append((int(re_match.group(1)), re_match.group(2)))
    return result


def get_command_history() -> str:
    history = os.environ.get("HISTORY")
    if history is None:
        raise EnvironmentError("Command history is not available. Check if alias is present.")
    return history


def read_stdin(forward_input: bool=True) -> str:
    output = ""
    for line in sys.stdin:
        if forward_input:
            print(line, end="", flush=True)
        output += line
    return output


"""Takes an iterable of Any and prints all strings as they arrive. Returns the full printed string"""
def print_ai_response(response_iter: Iterable[Any]) -> str:
    response = ""
    for chunk in response_iter:
        if isinstance(chunk, str):
            print(chunk, end="", flush=True)
            response += chunk
        
    print()
    return response


def welcome_message(session_id: int) -> str:
    return f"{abbreviation} command line assistant. Session {session_id}"


def shell(argv: Optional[Sequence[str]] = None) -> int:
    history = get_command_history()
    parsed_history = parse_command_history(history)
    last_command = parsed_history[-1][1]

    parser = get_arg_parser()
    args = parser.parse_args(argv)

    if args.switch_session == "interactive":
        raise NotImplementedError("This will be an interactive way to pick a session.")  # TODO: Implement
    if args.switch_session is not None and (not args.switch_session.isdigit() or int(args.switch_session) < 0):
        raise argparse.ArgumentTypeError("session id must be non-negative integer.")
    
    session_manager = SessionManager(Path(args.path), new_session=args.new_session)
    assistant = Assistant(session_manager, session_id=args.switch_session, verbose=args.verbose)

    print(welcome_message(assistant.session.id))
    if assistant.initial_message:
        print(assistant.initial_message)
    
    try:
        # Don't echo the input to the terminal, if the user didn't use a pipe.
        output = read_stdin(forward_input=not last_command.startswith(abbreviation))
    except KeyboardInterrupt:  # Just exit if the user presses Ctrl+C
        exit(0)
 
    cmd = CommandData(command=last_command, stdin=output, ai_response="")

    print_ai_response(assistant.new_command(cmd, give_ai_response=not args.listen))

    return 0

if __name__ == '__main__':
    exit(shell())  # pragma: no cover - I don't know to test this.
