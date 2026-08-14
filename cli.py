import argparse
from abbreviation import abbreviation
from pathlib import Path

def default_storage_path() -> Path:
    return Path.home() / f"{abbreviation}-assistant" / ".sessions"

def get_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=abbreviation)

    parser.add_argument("-l", "--listen", action="store_true", 
                        help="only take in the informantion, don't answer yet")
    
    parser.add_argument("-p", "--path", default=str(default_storage_path()), 
                        help=f"path to store session data. default is {str(default_storage_path())}")
    
    parser.add_argument("-n", "--new-session", action="store_true", 
                        help="start a new session")
    
    parser.add_argument("-s", "--switch-session", nargs="?", const="interactive", metavar="SESSION_ID",
                        help="switch to the session with the given id. no argument opens an interactive session selector (WIP)")
    
    parser.add_argument("-v", "--verbose", action="store_true", 
                        help="print debug info")
    parser.add_argument("-u", "--url", default="https://openrouter.ai/api/v1/chat/completions",
                        help="url for remote LLM api")
    return parser

