from dataclasses import dataclass, asdict
import json
from pathlib import Path
from typing import Self, Any
from abbreviation import abbreviation


# TODO: Change dataclasses to TypedDict
@dataclass
class CommandData:
    command: str
    stdin: str
    ai_response: str


@dataclass
class CommandSession:
    id: int
    prompt: str | None
    save_dir: str
    commands: list[CommandData]
    context: list[int]

    @classmethod
    def make_filename(cls: type[Self], id: int) -> str:
        return f"session.{id}.json"
    
    @property
    def filename(self) -> str:
        return self.make_filename(self.id)
    
    @property
    def path(self) -> Path:
        return Path(self.save_dir) / self.filename

    def save(self) -> None:
        self.path.write_text(json.dumps(asdict(self), indent=2))
    
    @classmethod
    def from_file(cls: type[Self], path: Path) -> Self:  # TODO: Add error handling when file doesn't exist
        session_dict = json.loads(path.read_text(encoding="utf-8"))
        
        if "commands" in session_dict:
            if not isinstance(session_dict["commands"], list):
                raise TypeError(f"'commands' must be a list, not a {type(session_dict['commands']).__name__}.\n{session_dict['commands']=}")
            session_dict["commands"] = [CommandData(**command) for command in session_dict["commands"]]
        else:
            raise ValueError(f"Session stored at {path}, has no 'commands' array.")

        return cls(**session_dict)
    
    @classmethod
    def from_id(cls: type[Self], save_dir: Path, id: int) -> Self:
        return cls.from_file(save_dir / cls.make_filename(id))


class SessionManager:
    path: Path
    sessions: list[CommandSession]

    def __init__(self, path: Path, new_session: bool = False):
        self.path = path
        self.path.mkdir(parents=False, exist_ok=True)
        self.sessions = []
        if new_session:
            self.sessions.append(self.create_new_session())
        

    def get_session_files(self) -> list[Path]:
        files = []
        for path in self.path.iterdir():
            if not path.is_file():
                continue
            parts = path.name.split('.')
            # filename must have the form "session.<number>.json"
            if len(parts) == 3 and parts[0] == "session" and parts[1].isdigit() and parts[2] == "json":
                files.append(path)
        return files

    def create_new_session(self, prompt: str | None = None) -> CommandSession:
        existing_ids = [int(p.name.split('.')[1]) for p in self.get_session_files()]
        new_id = (0 if not existing_ids else max(existing_ids) + 1)
        session = CommandSession(id=new_id, prompt=prompt, save_dir=str(self.path), commands=[], context=[])
        session.save()
        self.sessions.append(session)
        return session
        
    
    def load_most_recent_session(self) -> CommandSession:
        session_files = self.get_session_files()
        session_path = max(session_files, key=lambda p: p.stat().st_mtime, default=None)
        if session_path is None:
            return self.create_new_session()
        
        session = CommandSession.from_file(session_path)
        self.sessions.append(session)
        return session
    
    def load(self, session_id: int) -> CommandSession:
        return CommandSession.from_id(self.path, session_id)
