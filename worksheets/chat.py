from worksheets.environment import GenieContext
from worksheets.modules.agent_policy import run_agent_policy
from worksheets.modules.dialogue import CurrentDialogueTurn
from worksheets.modules.response_generator import generate_response
from worksheets.modules.semantic_parser import semantic_parsing


async def generate_next_turn(user_utterance: str, bot):
    """Generate the next turn in the dialogue based on the user's utterance.

    Args:
        user_utterance (str): The user's input.
        bot (Agent): The bot instance handling the dialogue.
    """
    # instantiate a new dialogue turn
    current_dlg_turn = CurrentDialogueTurn()
    current_dlg_turn.user_utterance = user_utterance

    # initialize contexts
    current_dlg_turn.context = GenieContext()
    current_dlg_turn.global_context = GenieContext()

    # process the dialogue turn to GenieWorksheets
    await semantic_parsing(current_dlg_turn, bot.dlg_history, bot)

    # run the agent policy if user_target is not None
    if current_dlg_turn.user_target is not None:
        run_agent_policy(current_dlg_turn, bot)

    # generate a response based on the agent policy
    await generate_response(current_dlg_turn, bot.dlg_history, bot)
    bot.dlg_history.append(current_dlg_turn)
