import chainlit as cl

from worksheets.annotation_utils import get_agent_action_schemas, get_context_schema
from worksheets.environment import GenieContext
from worksheets.modules.agent_policy import run_agent_policy
from worksheets.modules.dialogue import CurrentDialogueTurn
from worksheets.modules.response_generator import generate_response
from worksheets.modules.semantic_parser import semantic_parsing


async def generate_next_turn_cl(user_utterance: str, bot):
    """Generate the next turn in the dialogue based on the user's utterance for chainlit frontend.

    Args:
        user_utterance (str): The user's input.
        bot (Agent): The bot instance handling the dialogue.
    """

    # instantiate a new dialogue turn
    current_dlg_turn = CurrentDialogueTurn()
    current_dlg_turn.user_utterance = user_utterance

    # process the dialogue turn to GenieWorksheets
    async with cl.Step(
        name="Semantic Parsing",
        type="semantic_parser",
        language="python",
        show_input=True,
    ) as step:
        current_dlg_turn.context = GenieContext()
        current_dlg_turn.global_context = GenieContext()
        await semantic_parsing(current_dlg_turn, bot.dlg_history, bot)
        step.output = current_dlg_turn.user_target_sp

    # run the agent policy
    async with cl.Step(
        name="Using Agent Policy",
        type="agent_policy",
        language="python",
        show_input=True,
    ) as step:
        await cl.make_async(run_agent_policy)(current_dlg_turn, bot)
        step.input = current_dlg_turn.user_target
        step.output = get_agent_action_schemas(
            current_dlg_turn.system_action, bot.context
        )

    # generate a response based on the agent policy
    async with cl.Step(
        name="Generating Response",
        type="response_generator",
        language="python",
        show_input=True,
    ) as step:

        await generate_response(current_dlg_turn, bot.dlg_history, bot)
        step.output = get_context_schema(bot.context)
        bot.dlg_history.append(current_dlg_turn)
