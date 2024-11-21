import json

from worksheets.annotation_utils import get_agent_action_schemas, get_context_schema
from worksheets.chat import generate_next_turn
from worksheets.modules.dialogue import CurrentDialogueTurn


def convert_to_json(dialogue: list[CurrentDialogueTurn]):
    """Convert the dialogue history to a JSON-compatible format.

    Args:
        dialogue (list[CurrentDialogueTurn]): The dialogue history.

    Returns:
        list[dict]: The dialogue history in JSON format.
    """
    json_dialogue = []
    for turn in dialogue:
        json_turn = {
            "user": turn.user_utterance,
            "bot": turn.system_response,
            "turn_context": get_context_schema(turn.context),
            "global_context": get_context_schema(turn.global_context),
            "system_action": get_agent_action_schemas(turn.system_action),
            "user_target_sp": turn.user_target_sp,
            "user_target": turn.user_target,
            "user_target_suql": turn.user_target_suql,
        }
        json_dialogue.append(json_turn)
    return json_dialogue


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def input_user() -> str:
    """Prompt the user for input and return the input string."""
    try:
        user_utterance = input(bcolors.OKCYAN + bcolors.BOLD + "User: ")
        # ignore empty inputs
        while not user_utterance.strip():
            user_utterance = input(bcolors.OKCYAN + bcolors.BOLD + "User: ")
    finally:
        print(bcolors.ENDC)
    return user_utterance


def print_chatbot(s: str):
    """Print the chatbot's response in a formatted way."""
    print(bcolors.OKGREEN + bcolors.BOLD + "Agent: " + s + bcolors.ENDC)


def print_user(s: str):
    """Print the user's utterance in a formatted way."""
    print(bcolors.OKCYAN + bcolors.BOLD + "User: " + s + bcolors.ENDC)


def print_complete_history(dialogue_history):
    """Print the complete dialogue history."""
    for turn in dialogue_history:
        print_user(turn.user_utterance)
        print_chatbot(turn.system_response)


async def conversation_loop(bot, output_state_path, quit_commands=None):
    """Run the conversation loop with the chatbot. Dumps the dialogue history to a JSON file upon exit.

    Args:
        bot: The chatbot instance.
        output_state_path (str): The path to save the dialogue history.
        quit_commands (list[str], optional): List of commands to quit the conversation. Defaults to None.
    """
    print("inside conversation_loop in interface_utils.py")
    if quit_commands is None:
        quit_commands = ["exit", "exit()"]

    try:
        while True:
            if len(bot.dlg_history) == 0:
                print_chatbot(bot.starting_prompt)
            user_utterance = None
            if user_utterance is None:
                user_utterance = input_user()
            if user_utterance == quit_commands:
                break

            await generate_next_turn(user_utterance, bot)
            print_complete_history(bot.dlg_history)
    except Exception as e:
        print(e)

        import traceback

        traceback.print_exc()
    finally:
        with open(output_state_path, "w") as f:
            json.dump(convert_to_json(bot.dlg_history), f, indent=4)
