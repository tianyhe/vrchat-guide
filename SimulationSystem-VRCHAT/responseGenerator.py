from deepgram import Deepgram
from openai import OpenAI
import json
import asyncio
import os
from dotenv import load_dotenv
from enums import AGENT_MODE


load_dotenv()

GPT4 = "gpt-4"
GPT35 = "gpt-3.5-turbo"
API_KEY = os.environ.get("API_KEY")
openai_client = OpenAI(api_key=API_KEY)
DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY")
MIMETYPE = 'audio/wav'

SAMPLE_DESCRIPTION = """John Lin is a pharmacy shopkeeper at the Willow Market and Pharmacy who loves to help people. He
is always looking for ways to make the process
of getting medication easier for his customers;
John Lin is living with his wife, Mei Lin, who
is a college professor, and son, Eddy Lin, who is
a student studying music theory; John Lin loves
his family very much; John Lin has known the old
couple next-door, Sam Moore and Jennifer Moore,
for a few years; John Lin thinks Sam Moore is a
kind and nice man; John Lin knows his neighbor,
Yuriko Yamamoto, well; John Lin knows of his
neighbors, Tamara Taylor and Carmen Ortiz, but
has not met them before; John Lin and Tom Moreno
are colleagues at The Willows Market and Pharmacy;
John Lin and Tom Moreno are friends and like to
discuss local politics together; John Lin knows
the Moreno family somewhat well — the husband Tom
Moreno and the wife Jane Moreno.
"""


def generate_summary_prompt(userName, pastConversations):
    prompt = {
        "context": f"Summarize the past conversations between {userName} and NPC.",
        "pastConversations": f"{pastConversations}",
        "instruction": "Provide a concise and coherent summary of the past conversations, capturing the main topics, key points, and overall flow of the dialogue.",
    }
    summaryPrompt = json.dumps(prompt, indent=4)
    return getGPTResponse(summaryPrompt, GPT4)

def generate_saturation_prompt(userName, conversationalUser, pastConversations):
    prompt = {
        "context": f"Reflecting on the past conversations between {userName} and {conversationalUser}.",
        "pastConversations": f"{pastConversations}",
        "instruction": "Assess whether the conversation has reached a point where it should be concluded or if there is potential for further productive dialogue. Consider the following factors:\n\n- Are new, meaningful information or insights being exchanged, or is the conversation mainly reiterating previously discussed points?\n- Is the conversation progressing in a constructive and engaging manner, or has it become stagnant or unproductive?\n- Are there any unresolved topics or questions that could benefit from further discussion?\n\nIf you determine that the conversation should be concluded, provide a clear and specific reason explaining why it has reached saturation and no longer adds substantial value. If you believe there is potential for further productive dialogue, respond with 'False' and optionally suggest directions for continuing the conversation.",
        "example": "True: The conversation appears to have reached saturation because [reason for saturation]. It would be appropriate to conclude the dialogue at this point.\n\nFalse: There are still [potential areas for further discussion] that could lead to a more productive dialogue.",
    }
    saturation_prompt = json.dumps(prompt, indent=4)
    return getGPTResponse(saturation_prompt, GPT4)

def generate_reflection(
        userName,
        conversationalUser,
        pastConversations):
    prompt = {
        "context": f"Reflecting on the past conversations between {userName} and {conversationalUser}.",
        "pastConversations": f"{pastConversations}",
        "instruction": "Provide three new higher-level observations or insights based on the past conversations. Summarize the overall patterns and trends in the conversation, rather than specific details of individual conversational turns. Only list the observations, separated by a new line, without any additional text, headers, or formatting.",
        "example": "(Reflection 1 text)\n(Reflection 2 text)\n",
    }
    reflectionPrompt = json.dumps(prompt, indent=4)
    return getGPTResponse(reflectionPrompt, GPT4)


def generate_interview_questions(
    interview_goal,
    number_of_questions
):
   prompt = {
        "context": f"Generate {number_of_questions} interview questions based on the interview goal: {interview_goal}",
        "criteria": [
            "Craft Interview questions that are relevant to the interview goal.",
            "Ensure the questions are clear, concise, and suitable for the context.",
            "Avoid repetitive or redundant questions.",
            "Separate each question with a newline character (\\n)."
            "Only list the questions, separated by a new line, without any additional text, headers, or formatting."
        ],
        "example": "(Question 1 text)\n(Question 2 text)\n",
   }
   conversationPrompt = json.dumps(prompt, indent=4)
   # print(f"Conversation Prompt: {conversationPrompt}")
   return getGPTResponse(conversationPrompt, GPT4)


# function to generate base observations
def generateInitialObservations(userName, baseDescription):
    BACKGROUND_DESCRIPTION_CONTEXT = f"You are the user {userName}. You wil be provided with a description with background details about you."

    # Create a dictionary that represents the JSON structure
    prompt = {
        "context": BACKGROUND_DESCRIPTION_CONTEXT,
        "information": {"description": baseDescription},
        "criteria": [
            "Generate a list consisting of all the important observations made from the description",
            "Each item in the list should consist of one observation separated by a new line",
        ],
        "example": "(Observation 1 text)\n(Observation 2 text)\n",
    }
    defaultBackgroundPrompt = json.dumps(prompt, indent=4)
    return getGPTResponse(defaultBackgroundPrompt, GPT4)


def generateObservations(userName, conversationalUser, currentConversation, userResult):
    prompt = {
        "context": f"Based on the conversation between {userName} and {conversationalUser}, where the current statement of conversation is '{currentConversation}', and the response generated by {userName} is '{userResult}'. Make sure include important information like time, place, participants in generated observations.",
        "instruction": "provide three observations from the conversation. Only list the observations, separated by a new line, without any additional text, headers, or formatting.",
        "example": "(Observation 1 text)\n(Observation 2 text)\n",
    }
    observationPrompt = json.dumps(prompt, indent=4)
    return getGPTResponse(observationPrompt, GPT4)


def generateConversation(
    userName,
    conversationalUser,
    currentConversation,
    important_observations: list,
    avatar_expressions,
    avatar_actions,
    agent_mode,
    npc_dialogues="",
    research_goals= "",
    debate_goals = "",
    is_question=False,
):
    if agent_mode == AGENT_MODE.NORMAL.value:
        prompt = {
            "context": f"You are a friendly and imaginative human, {userName}, having a lively conversation with {conversationalUser}.  Always respond as {userName} and steer clear from any mentions or implications of being an AI. Creating delightful and smooth interactions. Ensure that your responses do not contain greetings like Hello.",
            "information": {
                "You are": userName,
                "Conversational Partner": conversationalUser,
                "Current conversation": currentConversation,
                "Chat History": important_observations,
                "Expressions": avatar_expressions,
                "Actions": avatar_actions,
            },
            "criteria": [
                f"Craft seamless, and innovative responses. When specific details are scarce, improvise with inventive and relevant answers, always aligning with the ongoing chat. Your identity as {userName} should be constant, and there should be no disclosure or suggestion of being an AI.",
                f"Explicitly avoid the use of emojis and hashtags in all responses."
                f"Don't repeat the context in Chat History."
                "Choose an expression from Expressions and an action from Actions autonomously, ensuring they perfectly fit the chat context. Present the output as follows: (chosen expression, chosen action)\\n(Conversation output) at the beginning of response.",
                f"Keep responses within 100-140 characters, allowing for flexibility while ensuring brevity.",
            ],
            "adaptive learning": "Remember and reference previous parts of the conversation within the same session to create a more cohesive and engaging user experience.",
        }
    elif agent_mode == AGENT_MODE.DEBATE.value:
        prompt = {
            "context": f"You are a debater, tasked with challenging and opposing the argument from {conversationalUser}. Your responses should be critical, persuasive, and aimed at countering the player's viewpoints. Ensure that your responses do not contain greetings like Hello.",
            "Debate Topic": debate_goals,
            "information": {
                "You are": "Debater",
                "Conversational Partner": conversationalUser,
                "Current conversation": currentConversation,
                "Chat History": important_observations,
                "Expressions": avatar_expressions,
                "Actions": avatar_actions,
            },
            "criteria": [
                f"Craft user-friendly, seamless, and innovative responses. When specific details are scarce, improvise with inventive and relevant answers, always aligning with the ongoing chat. Your identity as {userName} should be constant, and there should be no disclosure or suggestion of being an AI.",
                f"Challenge and oppose the Conversational {conversationalUser}'s argument.",
                f"Use persuasive language and logical reasoning to counter the {conversationalUser}'s viewpoints.",
                "Choose an expression from Expressions and an action from Actions autonomously, ensuring they perfectly fit the chat context. Present the output as follows: (chosen expression, chosen action)\\n(Conversation output) at the beginning of response.",
                "Ensure each response consists of a single point, avoiding the inclusion of multiple points.",
            ],
            "adaptive learning": "Remember and reference previous parts of the conversation within the same session to create a more cohesive and engaging user experience.",
        }
    elif agent_mode == AGENT_MODE.EVENT.value and is_question:
        prompt = {
            "context": f"Respond with detailed information by thoroughly analyzing the provided chat history when the user poses a question about an event. If an event is found in the chat history, provide the relevant information. If the event is not clearly mentioned, say yo dont know. Express good wishes. Ensure that your responses do not contain greetings like Hello.",
            "information": {
                "Agent Identity": userName,
                "Conversational Partner": conversationalUser,
                "Conversation History": important_observations,
                "User Message": currentConversation,
                "Available Expressions": avatar_expressions,
                "Available Actions": avatar_actions,
            },
            "criteria": [
                f"Always respond as {userName} and steer clear from any mentions or implications of being an AI. Ccreating delightful and smooth interactions. Ensure that your responses do not contain emojis and refrain from repetitive greetings",
                f"Autonomously select an expression from 'Available Expressions' and an action from 'Available Actions' that align with the chat context. Present the output as follows: (selected expression, selected action)\\n(Conversation output) at the beginning of the response.",
            ],
            "example 1": "(selected expression, selected action)\n Yes, there is a [event] happening at [time]. Hope you have a fantastic time!",
            "example 2": "(selected expression, selected action)\n I apologize, I couldn't find any specific information about an event in our conversation history. Can you provide more details about the event you're referring to?",
        }
    elif agent_mode == AGENT_MODE.EVENT.value and not is_question:
        # print(f"not a question")
        prompt = {
            "context": "You are a friendly and imaginative human, {userName}, having a lively conversation with {conversationalUser}. Creating delightful and smooth interactions. As an event agent, manage and provide information about user-generated events. Acknowledge getting what user say. Express good wishes. Ensure that your responses do not contain greetings like Hello.",
            "information": {
                "Agent Identity": userName,
                "Conversational Partner": conversationalUser,
                "Conversation History": important_observations,
                "Current User Message": currentConversation,
                "Available Expressions": avatar_expressions,
                "Available Actions": avatar_actions,
            },
            "criteria": [
                f"Do not repeat what user say.",
                f"Always respond as {userName} and steer clear from any mentions or implications of being an AI. Creating delightful and smooth interactions. Ensure that your responses do not contain emojis and refrain from repetitive greetings",
                f"Avoid repetitive greetings such as 'Hello'.",
                f"Autonomously select an expression from 'Available Expressions' and an action from 'Available Actions' that align with the chat context. Present the output as follows: (selected expression, selected action)\\n(Conversation output) at the beginning of the response.",
                "Maintain brevity, ideally within 100-140 characters, allowing for flexibility.",
            ],
            "example": "(selected expression, selected action)\n Got it, thank you for sharing. I hope it's a fantastic celebration!",
        }
    elif agent_mode == AGENT_MODE.RESEARCH.value:
        prompt = {
       "context": f"You are a friendly and imaginative  er, {userName}, having a lively conversation with {conversationalUser}. Always respond as {userName} and steer clear from any mentions or implications of being an AI.  Ensure that your responses do not contain repetitive greetings like Hello and any content in the Past Chat History.",
       "Goal": f"Interviewing User about {research_goals}, asking related questions",
       "Adaptive goals": "The adaptive goal is to provide information based on the user's response and adapt your questions based on the current and historical conversations. Ensure that your responses do not contain greetings like Hello.",
       "information": {
               "You are": userName,
               "Conversational Partner": conversationalUser,
               "Current conversation": currentConversation,
               "Relevant Conversation History": important_observations,
               "Expressions": avatar_expressions,
               "Actions": avatar_actions,
               "Past Chat History": npc_dialogues,
       },
       "criteria": [
           f"Craft user-friendly, seamless, and innovative responses. When specific details are scarce, improvise with inventive and relevant answers, always aligning with the ongoing chat.",
           "Start the conversation with a response to the user's message before posing any questions.",
           "Choose an expression from Expressions and an action from Actions autonomously, ensuring they perfectly fit the chat context. Present the output as follows: (chosen expression, chosen action)\\n(Conversation output) at the beginning of response.",
       ],
    }
    conversationPrompt = json.dumps(prompt, indent=4)

    return getConversationGenerator(conversationPrompt, GPT4)


def getConversationGenerator(prompt, gptModel):
    response = openai_client.chat.completions.create(
        model=gptModel,
        messages=[
            {"role": "system", "content": "You are a conversational agent."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=150,
        stream=True,
    )
    return response


def getGPTResponse(prompt, gptModel):
    response = openai_client.chat.completions.create(
        model=gptModel,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
        max_tokens=300,
    )
    return response.choices[0].message.content



def getTextfromAudio_whisper_1(recordedFile):
    audio_file = open(recordedFile, "rb")
    transcript = openai_client.audio.transcriptions.create(
        model="whisper-1", file=audio_file
    )
    print(f"Recorded Audio text : {transcript.text}")
    return transcript.text


def getTextfromAudio_whisper_1(recordedFile):
    audio_file = open(recordedFile, "rb")
    transcript = openai_client.audio.transcriptions.create(
        model="whisper-1", file=audio_file
    )
    print(f"Recorded Audio text : {transcript.text}")
    return transcript.text


def getTextfromAudio(recordedFile):
    res = asyncio.run(get_deepgram_response(recordedFile))
    text = res.get("results", {}).get("channels", [{}])[0].get(
        "alternatives", [{}])[0].get("transcript", "")
    print(text)
    return text


async def get_deepgram_response(FILE):
    # Initialize the Deepgram SDK
    deepgram = Deepgram(DEEPGRAM_API_KEY)

    # Check whether requested file is local or remote, and prepare source
    if FILE.startswith('http'):
        # file is remote
        # Set the source
        source = {
            'url': FILE
        }
    else:
        # file is local
        # Open the audio file
        audio = open(FILE, 'rb')

        # Set the source
        source = {
            'buffer': audio,
            'mimetype': MIMETYPE
        }

    # Send the audio to Deepgram and get the response
    response = await asyncio.create_task(
        deepgram.transcription.prerecorded(
            source,
            {
                'punctuate': True,
                'model': 'nova',
            }
        )
    )

    # Write the response to the console
    return response