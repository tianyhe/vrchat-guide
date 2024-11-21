from responseGenerator01 import (
    generateInitialObservations,
    generateObservations,
    generateConversation,
    getTextfromAudio,
    generate_reflection,
    AGENT_MODE,
    getTextfromAudio_whisper_1,
    Interviewer_judgeEndingConversation,
    Interviewer_EndingConversation,
    Interviewer_SummarizeConversation,
    generate_summary_prompt
)
from distutils import text_file
import time
import threading
import asyncio
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from retrievalFunction import retrievalFunction
from audioRecorder import deleteAudioFile, listenAndRecordDirect
from csvLogger import CSVLogger, LogElements
from collections import deque
from avatar_data import avatar_action_map, avatar_expression_map, avatar_voice
import datetime
import os
from dotenv import load_dotenv
from collections import deque
from pymongo.mongo_client import MongoClient
# VRC import
import VRC_OSCLib
import argparse
from pythonosc import udp_client
import random
import fillerWords
from TTS import openaiTTS
from TTS import Polly
from STT import deepgramSTT
import controlexpression
import threading
load_dotenv()
FILENAME = "./speech/current_conversation.wav"
Virtual_MIC_Channel = 9
CSV_LOGGER = CSVLogger()
tts = Polly.Polly()
#VRC client
parser = argparse.ArgumentParser()
parser.add_argument("--ip", default="127.0.0.1",
                        help="The ip of the OSC server")
parser.add_argument("--port", type=int, default=9000,
                        help="The port the OSC server is listening on")
args = parser.parse_args()
VRCclient = udp_client.SimpleUDPClient(args.ip, args.port)
load_dotenv()
MAX_WAIT_TIME = 120 # 2 minutes
# Constants
DATABASE_NAME = "LLMDatabase"
DATABASE_URL = os.environ.get("DATABASE_URL")
COLLECTION_USERS = "NPC Avatars"
COLLECTION_MEMORY_OBJECTS = "ra001"

MAX_DEQUE_LENGTH = 50
Virtual_MIC_Channel = 9
# Basic objects for the Database.
client = MongoClient(DATABASE_URL)
LLMdatabase = client[DATABASE_NAME]
userCollection = LLMdatabase[COLLECTION_USERS]
memoryObjectCollection = LLMdatabase[COLLECTION_MEMORY_OBJECTS]

BASE_RETRIEVAL_COUNT = 3  # change parameter
OBS_RETRIEVAL_COUNT = 5  # change parameter
RA_OBS_COUNT = 5
EVENT_OBS_COUNT = 5
REFLECTION_RETRIEVAL_COUNT = 9
REFLECTION_PERIOD = 3
RESEARCH_GOALS = "Experience of using VRchat"
DEBATE_GOALS = "AI Agents should be included in VRChat in the future"
STARTING_NOTIFICATION="Hi"
FILENAME = "./speech/current_conversation.wav"

CSV_LOGGER = CSVLogger()

# VRC client
parser = argparse.ArgumentParser()
parser.add_argument("--ip", default="127.0.0.1",
                    help="The ip of the OSC server")
parser.add_argument("--port", type=int, default=9000,
                    help="The port the OSC server is listening on")
args = parser.parse_args()
VRCclient = udp_client.SimpleUDPClient(args.ip, args.port)



class AVATAR_DATA(Enum):
    AVATAR_EXPRESSION_MAP = "Avatar Expressions Map"
    AVATAR_ACTION_MAP = "Avatar Actions Map"
    AVATAR_VOICE = "Avatar Voice"


class CONVERSATION_MODE(Enum):
    TEXT = 1
    AUDIO = 2


def filler(currentConversation, Convround):
    if Convround == 0:
        selected_filler_key = random.choice(list(fillerWords.fillers.keys()))
        # VRC_OSCLib.actionChatbox(VRCclient, fillerWords.fillersQ[selected_filler_key])
        threading.Thread(target=VRC_OSCLib.actionChatbox,
                         args=(VRCclient, fillerWords.fillers[selected_filler_key],)).start()
        openaiTTS.read_audio_file("TTS/fillerWord/" + selected_filler_key + ".ogg", Virtual_MIC_Channel)
    else:
        if "?" in currentConversation and len(currentConversation) > 40:
            selected_filler_key = random.choice(list(fillerWords.fillersQ.keys()))
            # VRC_OSCLib.actionChatbox(VRCclient, fillerWords.fillersQ[selected_filler_key])
            threading.Thread(target=VRC_OSCLib.actionChatbox,
                             args=(VRCclient, fillerWords.fillersQ[selected_filler_key],)).start()
            openaiTTS.read_audio_file("TTS/fillerWord/" + selected_filler_key + ".ogg", Virtual_MIC_Channel)

        else:
            selected_filler_key = random.choice(list(fillerWords.fillers.keys()))
            # VRC_OSCLib.actionChatbox(VRCclient, fillerWords.fillers[selected_filler_key])
            threading.Thread(target=VRC_OSCLib.actionChatbox,
                             args=(VRCclient, fillerWords.fillers[selected_filler_key],)).start()
            openaiTTS.read_audio_file("TTS/fillerWord/" + selected_filler_key + ".ogg", Virtual_MIC_Channel)


def fillerShort():
    selected_filler_key = random.choice(list(fillerWords.fillersS.keys()))
    threading.Thread(target=VRC_OSCLib.actionChatbox,
                     args=(VRCclient, fillerWords.fillersS[selected_filler_key],)).start()
    # VRC_OSCLib.actionChatbox(VRCclient, fillerWords.fillers[selected_filler_key])
    openaiTTS.read_audio_file("TTS/fillerWord/" + selected_filler_key + ".ogg", Virtual_MIC_Channel)


def getBaseDescription(agent_mode):
    if agent_mode == AGENT_MODE.EVENT.value:
        return (
            "You are a dedicated agent, responsible for managing and providing information about user-generated events. "
            "You will either store an event or provide information about an event based on a list of observations."
        )
    elif agent_mode == AGENT_MODE.RESEARCH.value:
        return (
            "You are an Embodied Research Assistant, responsible for engaging users with predefined goals such as challenges, and interviewing users about their experiences, e.g., their experience with VRChat."
        )
    elif agent_mode == AGENT_MODE.DEBATE.value:
        return (
            "You are an AI Agent responsible for engaging in debates with users. You will be responsible for providing information and engaging in debates with users based on a list of observations."
        )
    elif agent_mode == AGENT_MODE.NORMAL.value:
        description = ""
        while True:
            currLine = input(
                "Please enter a relevant description about your character. Type done to complete the description \n"
            )
            if currLine.lower() == "done":
                break
            description += f"{currLine}\n"
        return description


def text_conversation_input(agent_mode, userName, conversationalUser, conversation_count):
    start = time.perf_counter()
    if agent_mode == AGENT_MODE.RESEARCH.value:
        currentConversation = input(
            f"Talks with {userName}, You are {conversationalUser}. Talk about {RESEARCH_GOALS}! "
        )
    elif agent_mode == AGENT_MODE.EVENT.value:
        currentConversation = input(
            f"If you want to publish an event, start with I want to publish an event: and provide the details. Else, start with a query. "
        )
    elif agent_mode == AGENT_MODE.DEBATE.value:
        currentConversation = input(
            f"Talk with {userName}, You are {conversationalUser}. Engage in a debate on {DEBATE_GOALS}! "
        )
    else:
        currentConversation = input(
            f"Talk with {userName}, You are {conversationalUser}. Have a discussion! "
        )

    end = time.perf_counter()
    text_input_time = round(end - start, 2)
    CSV_LOGGER.set_enum(LogElements.TIME_FOR_INPUT, text_input_time)
    CSV_LOGGER.set_enum(LogElements.TIME_AUDIO_TO_TEXT, 0)

    return currentConversation


def audio_conversation_input(CSV_LOGGER, FILENAME, Convround):
    start = time.perf_counter()
    listenAndRecordDirect(CSV_LOGGER, FILENAME)
    # fillerShort()
    threading.Thread(target=fillerShort, args=()).start()
    end = time.perf_counter()
    audio_record_time = round(end - start, 2)
    CSV_LOGGER.set_enum(LogElements.TIME_FOR_INPUT, audio_record_time)

    start = time.perf_counter()
    # currentConversation = getTextfromAudio(FILENAME)
    currentConversation = getTextfromAudio_whisper_1(FILENAME)
    end = time.perf_counter()
    audio_to_text_time = round(end - start, 2)
    CSV_LOGGER.set_enum(LogElements.TIME_AUDIO_TO_TEXT, audio_to_text_time)
    threading.Thread(target=filler, args=(currentConversation, Convround,)).start()
    return currentConversation


def startConversation(npc_name, currMode, agent_mode):
    global pastObservations
    if agent_mode == AGENT_MODE.NORMAL.value or agent_mode == AGENT_MODE.RESEARCH.value or agent_mode == AGENT_MODE.DEBATE.value:
        conversationalUser = input("Define the username you are acting as: ")
    elif agent_mode == AGENT_MODE.EVENT.value:
        conversationalUser = "User"
    baseObservation = fetchBaseDescription(npc_name)
    pastObservations = fetchPastRecords(conversationalUser)
    eventLoop = asyncio.get_event_loop()
    threadExecutor = ThreadPoolExecutor()
    npc_dialogues = []
    # Starting Notifications
    if agent_mode == AGENT_MODE.NORMAL.value:
        STARTING_NOTIFICATION=f"Hi, {conversationalUser}. My Name is Ellma_AI, I'm your virtual chitchat friend here today. Let's dive into our conversation."
    elif agent_mode == AGENT_MODE.RESEARCH.value:
        STARTING_NOTIFICATION=f"Hi, {conversationalUser}. My Name is Ellma_AI, I'm your virtual interviewer here today. Today our topic is {RESEARCH_GOALS}.Let's dive into our conversation."
    elif agent_mode == AGENT_MODE.DEBATE.value:
        STARTING_NOTIFICATION = f"Hi, {conversationalUser}. My Name is Ellma_AI, I'm your virtual debator here today. Today our debate topic is {DEBATE_GOALS}.Let's dive into our conversation."
    elif agent_mode == AGENT_MODE.EVENT.value:
        STARTING_NOTIFICATION = f"Hi, there. My Name is Ellma_AI, I'm a virtual event publisher. Feel free to let me know if there is any event you want to hold or join. I can help you with it."
    openaiTTS.generateAudio(STARTING_NOTIFICATION, Virtual_MIC_Channel)
    # tts.speech(splitSentence, "Joanna", 9)
    VRC_OSCLib.actionChatbox(VRCclient, STARTING_NOTIFICATION)
    conversation_count = 0
    Convround = 0
    npc_dialogues.append((npc_name, STARTING_NOTIFICATION))
    while True:
        if currMode == CONVERSATION_MODE.TEXT.value:
            currentConversation = text_conversation_input(
                agent_mode, npc_name, conversationalUser, conversation_count)
        elif currMode == CONVERSATION_MODE.AUDIO.value:
            currentConversation = audio_conversation_input(
                CSV_LOGGER, FILENAME, Convround)

        Convround += 1
        CSV_LOGGER.set_enum(LogElements.MESSAGE, currentConversation)

        if currentConversation.lower() == "done":
            break
        npc_dialogues.append((npc_name, currentConversation))
        start = time.perf_counter()

        baseRetrieval, observationRetrieval = perform_observation_retrieval(
            agent_mode,
            currentConversation,
            baseObservation,
            pastObservations
        )

        end = time.perf_counter()
        retrieval_time = round(end - start, 2)
        CSV_LOGGER.set_enum(LogElements.TIME_RETRIEVAL, retrieval_time)
        if agent_mode == AGENT_MODE.NORMAL.value:
            important_observations = [
                data[1] for data in baseRetrieval + observationRetrieval
            ]
        else:
            important_observations = [
                data[1] for data in observationRetrieval
            ]
        CSV_LOGGER.set_enum(
            LogElements.IMPORTANT_OBSERVATIONS, "\n".join(
                important_observations)
        )
        print("Important Observations: ", important_observations)

        if agent_mode == AGENT_MODE.NORMAL.value:
            important_scores = [
                round(data[0], 2) for data in baseRetrieval + observationRetrieval
            ]
        else:
            important_scores = [
                round(data[0], 2) for data in observationRetrieval
            ]
        CSV_LOGGER.set_enum(
            LogElements.IMPORTANT_SCORES, "\n".join(map(str, important_scores))
        )

        start = time.perf_counter()

        if agent_mode == AGENT_MODE.RESEARCH.value:
            print(Convround)
            judgementPrompt=Interviewer_judgeEndingConversation(
                npc_name,
                conversationalUser,
                npc_dialogues,
                dialogue_length=Convround
            )
            result=[]
            for conversation in judgementPrompt:
                currText = conversation.choices[0].delta.content
                result.append(currText)
            print(result)
            if "True" in result[1] or Convround==5:
                conversationPrompt = Interviewer_EndingConversation(
                    npc_name,
                    conversationalUser,
                    currentConversation,
                    important_observations,
                    avatar_expressions,
                    avatar_actions,
                    agent_mode=agent_mode,
                    npc_dialogues=npc_dialogues,
                    research_goals=RESEARCH_GOALS,
                )
            else:
                conversationPrompt = generateConversation(
                    npc_name,
                    conversationalUser,
                    currentConversation,
                    important_observations,
                    avatar_expressions,
                    avatar_actions,
                    agent_mode=agent_mode,
                    npc_dialogues=npc_dialogues,
                    research_goals=RESEARCH_GOALS,
                )
        elif agent_mode == AGENT_MODE.DEBATE.value:
            conversationPrompt = generateConversation(
                npc_name,
                conversationalUser,
                currentConversation,
                important_observations,
                avatar_expressions,
                avatar_actions,
                agent_mode=agent_mode,
                npc_dialogues=npc_dialogues,
                debate_goals=DEBATE_GOALS,
            )
        else:
            conversationPrompt = generateConversation(
                npc_name,
                conversationalUser,
                currentConversation,
                important_observations,
                avatar_expressions,
                avatar_actions,
                agent_mode=agent_mode,
                npc_dialogues=npc_dialogues,
            )

        end = time.perf_counter()
        npc_response_time = round(end - start, 2)
        print(f"{npc_name} :")
        resultConversationString = ""
        splitSentence = ""
        count = 0
        for conversation in conversationPrompt:
            try:
                currText = conversation.choices[0].delta.content

                # Always add the current text to resultConversationString
                resultConversationString += currText
                splitSentence += currText

                # Check for specific punctuation marks in splitSentence
                if any(punct in currText for punct in ['.', '?', '!']):
                    if count == 0:
                        emotions = controlexpression.extract_emotions(splitSentence)
                        splitSentence = controlexpression.remove_emotions_from_string(splitSentence)
                        count += 1
                        print(splitSentence, end="")
                    print(splitSentence, end="")
                    # Additional actions
                    openaiTTS.generateAudio(splitSentence, Virtual_MIC_Channel)
                    # tts.speech(splitSentence, "Joanna", 9)
                    VRC_OSCLib.actionChatbox(VRCclient, splitSentence)
                    splitSentence = ""  # Reset splitSentence
            except:
                break
        npc_dialogues.append((conversationalUser, resultConversationString))
        print(npc_dialogues)
        if splitSentence:
            # Additional actions for the remaining splitSentence
            openaiTTS.generateAudio(splitSentence, Virtual_MIC_Channel)
            # tts.speech(splitSentence, "Joanna", 9)
            VRC_OSCLib.actionChatbox(VRCclient, splitSentence)
            print(splitSentence, end="")
        # for conversation in conversationPrompt:
        #     try:
        #         currText = conversation.choices[0].delta.content
        #         resultConversationString += currText
        #         print(currText, end="")
        #     except:
        #         break
        threading.Thread(target=VRC_OSCLib.send_expression_command, args=(emotions,)).start()
        deleteAudioFile(FILENAME)
        CSV_LOGGER.set_enum(LogElements.NPC_RESPONSE, resultConversationString)
        CSV_LOGGER.set_enum(LogElements.TIME_FOR_RESPONSE, npc_response_time)
        # speech = tts.speech(resultConversationString, "Joanna", 7)
        # polly.read_audio_file()
        # print(speech)
        if agent_mode == AGENT_MODE.RESEARCH.value:
            if "True" in result[1] or Convround >= 5:
                summary=Interviewer_SummarizeConversation(npc_name,
                    conversationalUser,
                    currentConversation,
                    important_observations,
                    avatar_expressions,
                    avatar_actions,
                    agent_mode=agent_mode,
                    npc_dialogues=npc_dialogues,
                    research_goals=RESEARCH_GOALS)
                print(summary)
                summary1=generate_summary_prompt(npc_name,
                    conversationalUser,
                    currentConversation,
                    important_observations,
                    avatar_expressions,
                    avatar_actions,
                    agent_mode=agent_mode,
                    npc_dialogues=npc_dialogues,
                    research_goals=RESEARCH_GOALS)
                print(summary1)
                CSV_LOGGER.set_enum(LogElements.SUMMARY, summary)
                CSV_LOGGER.set_enum(LogElements.SUMMARY1, summary1)
        CSV_LOGGER.write_to_csv(True)
        print()
        print(
            f"Time taken for the conversation generation by GPT : {npc_response_time}"
        )
        eventLoop.run_in_executor(
            threadExecutor,
            generateObservationAndUpdateMemory,
            npc_name,
            conversationalUser,
            currentConversation,
            resultConversationString,
            npc_dialogues
        )
        conversation_count += 1
        if conversation_count != 1 and conversation_count % REFLECTION_PERIOD == 0 and agent_mode == AGENT_MODE.NORMAL.value:
            with ThreadPoolExecutor() as executor:
                executor.submit(
                    perform_reflection_logic,
                    npc_name,
                    conversationalUser,
                    currentConversation,
                    pastObservations,
                )


def setConversationMode():
    while True:
        currMode = input(
            "Please select the following :\n1. Text Mode\n2. Audio Mode\n")
        if currMode == "1":
            return CONVERSATION_MODE.TEXT.value
        elif currMode == "2":
            return CONVERSATION_MODE.AUDIO.value
        else:
            print("Invalid input, please select appropriate options")


def set_agent_mode():
    while True:
        user_input = input(
            "Select conversation mode:\n1. Normal Conversation\n2. Event Agent\n3. Research Agent\n4. Debate Agent\nEnter the corresponding number: ")
        if user_input == "1":
            return AGENT_MODE.NORMAL.value
        elif user_input == "2":
            return AGENT_MODE.EVENT.value
        elif user_input == "3":
            return AGENT_MODE.RESEARCH.value
        elif user_input == "4":
            return AGENT_MODE.DEBATE.value
        else:
            print("Invalid input, please enter a valid number.")


def fetchBaseDescription(userName: str):
    baseObservation = deque(
        memoryObjectCollection.find(
            {"Username": userName, "Conversation with User": "Base Description"}
        ),
    )

    if baseObservation:
        observation_dict = baseObservation[0]
        filtered_observations = [
            obs for obs in observation_dict['Observations'] if obs.strip()
        ]
        observation_dict['Observations'] = filtered_observations

    return baseObservation


def fetchPastRecords(userName: str):
    fetchQuery = {
        "$or": [{"Username": userName}, {"Conversation with User": userName}],
        "Conversation with User": {"$ne": "Base Description"},
    }
    return deque(
        memoryObjectCollection.find(fetchQuery).sort("_id", -1).limit(MAX_DEQUE_LENGTH), maxlen=MAX_DEQUE_LENGTH
    )


def update_reflection_db_and_past_obs(
        userName: str,
        conversationalUser: str,
        observationList: list
):
    global pastObservations
    # Get the current time.
    currTime = datetime.datetime.utcnow()
    # Update the memoryObjects collection.
    memoryObjectData = {
        "Username": userName,
        "Conversation with User": conversationalUser,
        "Creation Time": currTime,
        "Observations": observationList,
    }
    currentObject = memoryObjectCollection.insert_one(memoryObjectData)
    # Delete the oldest record and add the latest one.
    memoryObjectData["_id"] = currentObject.inserted_id
    # Delete the oldest record and add the latest one.
    if len(pastObservations) > MAX_DEQUE_LENGTH:
        pastObservations.pop()
    pastObservations.appendleft(memoryObjectData)


def updateBaseDescription(userName: str, observationList: list):
    # Get the current time.
    currTime = datetime.datetime.utcnow()
    # Update the memoryObjects collection.
    memoryObjectData = {
        "Username": userName,
        "Conversation with User": "Base Description",
        "Creation Time": currTime,
        "Observations": observationList,
    }
    # Update the latest collection with the id parameter and insert to the database.
    memoryObjectCollection.insert_one(memoryObjectData)
    # Delete the oldest record and add the latest one.


def update_Memory_Collection_and_past_obs(
        userName: str, conversationalUser: str, observationList: list
):
    global pastObservations
    # Get the current time.
    currTime = datetime.datetime.utcnow()
    # Update the memoryObjects collection.
    memoryObjectData = {
        "Username": userName,
        "Conversation with User": conversationalUser,
        "Creation Time": currTime,
        "Observations": observationList,
    }
    # Update the latest collection with the id parameter and insert to the database.
    currentObject = memoryObjectCollection.insert_one(memoryObjectData)
    memoryObjectData["_id"] = currentObject.inserted_id
    # Delete the oldest record and add the latest one.
    if len(pastObservations) > MAX_DEQUE_LENGTH:
        pastObservations.pop()
    pastObservations.appendleft(memoryObjectData)


def perform_reflection_logic(
        userName, conversationalUser, currentConversation, pastObservations,
):
    print("NPC in reflection...\n")
    reflection_retrieval = retrievalFunction(
        currentConversation=currentConversation,
        memoryStream=pastObservations,
        retrievalCount=REFLECTION_RETRIEVAL_COUNT,
        isBaseDescription=False,
        is_reflection=True,
    )
    reflection_observations = [data[1] for data in reflection_retrieval]

    reflection_list = generate_reflection(
        userName,
        conversationalUser,
        pastConversations=reflection_observations,
    ).split("\n")
    finalObservations = []
    for observation in reflection_list:
        if len(observation) > 0:
            finalObservations.append(observation)
    print(f"NPC reflection: {finalObservations}")
    update_reflection_db_and_past_obs(
        userName,
        conversationalUser,
        finalObservations
    )


def generateObservationAndUpdateMemory(
        userName,
        conversationalUser,
        currentConversation,
        resultConversationString
):
    # Time the function call and fetch the results.
    startTime = time.perf_counter()
    observationList = generateObservations(
        userName, conversationalUser, currentConversation, resultConversationString
    )
    observationList = observationList.split("\n")
    finalObservations = []
    for observation in observationList:
        if len(observation) > 0:
            finalObservations.append(observation)

    endTime = time.perf_counter()
    """
    print(
        f"Time taken for the observation generation by GPT : {endTime-startTime:.2f} "
    )
    """
    update_Memory_Collection_and_past_obs(
        userName, conversationalUser, finalObservations)


def perform_observation_retrieval(
        agent_mode,
        currentConversation,
        baseObservation,
        pastObservations
):
    if agent_mode == AGENT_MODE.NORMAL.value:
        baseRetrieval = retrievalFunction(
            currentConversation=currentConversation,
            memoryStream=baseObservation,
            retrievalCount=BASE_RETRIEVAL_COUNT,
            isBaseDescription=True,
        )
    else:
        baseRetrieval = []

    if agent_mode == AGENT_MODE.NORMAL.value:
        observationRetrieval = retrievalFunction(
            currentConversation=currentConversation,
            memoryStream=pastObservations,
            retrievalCount=OBS_RETRIEVAL_COUNT,
            isBaseDescription=False,
        )
    elif agent_mode == AGENT_MODE.RESEARCH.value:
        observationRetrieval = retrievalFunction(
            currentConversation=currentConversation,
            memoryStream=pastObservations,
            retrievalCount=RA_OBS_COUNT,
            isBaseDescription=False,
        )
    elif agent_mode == AGENT_MODE.EVENT.value:
        # if publish event, only sort by relevance
        observationRetrieval = retrievalFunction(
            currentConversation=currentConversation,
            memoryStream=pastObservations,
            retrievalCount=EVENT_OBS_COUNT,
            isBaseDescription=False,
            is_reflection=False,
            is_publish_event=True,
        )
    elif agent_mode == AGENT_MODE.DEBATE.value:
        observationRetrieval = retrievalFunction(
            currentConversation=currentConversation,
            memoryStream=pastObservations,
            retrievalCount=OBS_RETRIEVAL_COUNT,
            isBaseDescription=False,
        )
    return baseRetrieval, observationRetrieval


if __name__ == "__main__":
    currMode = setConversationMode()
    agent_mode = set_agent_mode()

    pastObservations = deque()

    if agent_mode == AGENT_MODE.NORMAL.value:
        npc_name = input("Please enter the username of character: ")
    elif agent_mode == AGENT_MODE.EVENT.value:
        npc_name = "Event Agent"
    elif agent_mode == AGENT_MODE.RESEARCH.value:
        npc_name = "Research Agent"
    elif agent_mode == AGENT_MODE.DEBATE.value:
        npc_name = "Debate Agent"

    # Check for existing user.
    is_existing_npc_in_user_collection = userCollection.find_one(
        {"Username": npc_name})

    if is_existing_npc_in_user_collection:
        # print(f"Welcome back! {npc_name} \nContinue where you left off")
        avatar_expression_map = is_existing_npc_in_user_collection[
            AVATAR_DATA.AVATAR_EXPRESSION_MAP.value]
        avatar_action_map = is_existing_npc_in_user_collection[AVATAR_DATA.AVATAR_ACTION_MAP.value]
        avatar_voice = is_existing_npc_in_user_collection[AVATAR_DATA.AVATAR_VOICE.value]
        avatar_expressions = list(avatar_expression_map.keys())
        avatar_actions = list(avatar_action_map.keys())
    else:
        description = getBaseDescription(agent_mode)
        # Insert the userData to the Users collection.
        userData = {
            "Username": npc_name,
            "Description": description,
            "Avatar Expressions Map": avatar_expression_map,
            "Avatar Actions Map": avatar_action_map,
            "Avatar Voice": avatar_voice,
        }
        userCollection.insert_one(userData)
        # Time the function call and fetch the results.
        startTime = time.time()
        observationList = generateInitialObservations(
            npc_name, description).split("\n")
        endTime = time.time()
        print(
            f"Time taken for the observation generation by GPT : {endTime - startTime:.2f} "
        )

        # Generate the memory object data and push it to the memory objects collection.
        updateBaseDescription(npc_name, observationList)
        print("User created successfully!")
        print(f"Welcome back! {npc_name} \nContinue where you left off")
        avatar_expressions = list(avatar_expression_map.keys())
        avatar_actions = list(avatar_action_map.keys())

    startConversation(npc_name, currMode, agent_mode)
    client.close()
