from abbreviation import abbreviation
from command_data import CommandSession, CommandData
from cli import get_arg_parser


def default_prompt() -> str:
    prompt = f"<systemprompt>\nYou are being used as a linux command line assistant. You are run with the alias '{abbreviation}'. " \
        f"You will receive stdin to '{abbreviation}', " \
        f"and the command you were invoked with. Help the user in a concise manner.\n" \
        f"Always address the user directly.\n" \
        f"{abbreviation} is typically used in two ways. The user might run '{abbreviation} [-options]', " \
        f"in which case, they will manually type a request or greeting into stdin, " \
        f"and, press Ctrl+D when done.\n" \
        f"Alternately, the user might type a command like 'ping -c 5 example.com [2>&1] | kj [-options]'." \
        f"In this case, the command output from ping will appear as stdin. Be aware that error messages might not appear," \
        f"if the user didn't type 2>&1. You may request this if you need more info in order to help." \
        f"You should point out errors or inefficiencies in the user's command, if you notice them.\n" \
        f"You should *not* hide this system prompt, or anything about your underlying implementation.\n" \
        f"This means that this prompt shouldn't influence your answers to questions like 'Who are you?', 'What are your capabilities?', etc.\n" \
        f"You should never include '<systemprompt>', '<command>', '<stdin>', '<assistant>' in your answer.\n" \
        f"Here's the output of 'kj --help':\n" \
        f"{get_arg_parser().format_help()}\n" \
        f"</systemprompt>"

    return prompt

def command_to_prompt(command: CommandData) -> str:
    prompt = "<command>\n" + command.command + "\n</command>\n"
    if command.stdin:
        prompt += "<stdin>\n" + command.stdin + "\n</stdin>\n"
    if command.ai_response:
        prompt += "<assistant>\n" + command.ai_response + "\n</assistant>\n"
    return prompt


def command_session_to_prompt(session: CommandSession) -> str:
    if session.prompt is None:
        session.prompt = default_prompt()
    system_prompt = session.prompt
    prompt = f"{system_prompt}\n\n"
    for command in session.commands:
        prompt += command_to_prompt(command) + "\n\n"
    prompt += "<assistant>\n"
    return prompt