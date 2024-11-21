import datetime
import json
from typing import List

from bs4 import BeautifulSoup

from worksheets.annotation_utils import get_agent_action_schemas, get_context_schema
from worksheets.llm.basic import llm_generate
from worksheets.modules import CurrentDialogueTurn


async def generate_response(
    current_dlg_turn: CurrentDialogueTurn, dlg_history: List[CurrentDialogueTurn], bot
):
    # Gather the schema for the current state
    state_schema = get_context_schema(bot.context, response_generator=True)

    # Get the agent actions based on the current dialogue turn
    if current_dlg_turn.system_action is None:
        agent_acts = []
    else:
        agent_acts = get_agent_action_schemas(
            current_dlg_turn.system_action, bot.context
        )

    # Determine the previous agent utterance
    if len(dlg_history):
        agent_utterance = dlg_history[-1].system_response
    else:
        agent_utterance = bot.starting_prompt

    # Prepare the inputs for the prompt
    prompt_inputs = {
        "prior_agent_utterance": agent_utterance,
        "user_utterance": current_dlg_turn.user_utterance,
        "dlg_history": dlg_history,
        "bot": bot,
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "day": datetime.datetime.now().strftime("%A"),
        "state": state_schema,
        "agent_acts": json.dumps(agent_acts, indent=2),
        "description": bot.description,
        "parsing": current_dlg_turn.user_target,
    }

    # Generate the agent's response
    agent_response = await llm_generate(
        "response_generator.prompt",
        prompt_inputs=prompt_inputs,
        prompt_dir=bot.prompt_dir,
        model_name="gpt-4o",
        # **bot.args["response_generator"],
    )

    current_dlg_turn.system_response = agent_response


# TODO: We are not using this, but should make this better
def response_supervisor(agent_response, prompt_inputs):
    prompt_inputs["agent_response"] = agent_response
    agent_response = llm_generate(
        "supervisor_response_generator.prompt",
        prompt_inputs=prompt_inputs,
        model_name="gpt-4o",
    )

    bs = BeautifulSoup(agent_response, "html.parser")
    answer = bs.find("answer")
    feedback = bs.find("reasoning")

    if answer is not None:
        answer = answer.text.lower().strip()
        if answer == "true":
            answer = True
        else:
            answer = False
    if feedback is not None:
        feedback = feedback.text.lower().strip()

    return answer, feedback
