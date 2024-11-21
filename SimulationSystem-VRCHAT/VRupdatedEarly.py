from responseGenerator import *
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from retrievalFunction import retrievalFunction
from audioRecorder import listenAndRecordDirect, deleteAudioFile
from csvLogger import CSVLogger, LogElements
from collections import deque
from avatar_data import avatar_action_map, avatar_expression_map, avatar_voice
import datetime
import os
from dotenv import load_dotenv
from collections import deque
from pymongo.mongo_client import MongoClient
from dialoge_helper import filter_conversation, is_question_function, perform_summurization_logic, setConversationMode, set_agent_mode, getBaseDescription, getBaseDescription, select_important_observations, calculate_important_scores, perform_observation_retrieval, perform_saturation_logic, generate_conversation_helper, RESEARCH_GOALS, DEBATE_GOALS, write_to_file
from enums import CONVERSATION_MODE, AGENT_MODE, AVATAR_DATA
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
# Constants
DATABASE_NAME = "LLMDatabase"
DATABASE_URL = os.environ.get("DATABASE_URL")
COLLECTION_USERS = "NPC Avatars"
COLLECTION_MEMORY_OBJECTS = "ev013"

MAX_DEQUE_LENGTH = 50

# Basic objects for the Database.
client = MongoClient(DATABASE_URL)
LLMdatabase = client[DATABASE_NAME]
userCollection = LLMdatabase[COLLECTION_USERS]
memoryObjectCollection = LLMdatabase[COLLECTION_MEMORY_OBJECTS]


BASE_RETRIEVAL_COUNT = 3  # change parameter
OBS_RETRIEVAL_COUNT = 5  # change parameter
RA_OBS_COUNT = 5
EVENT_OBS_COUNT = 5
REFLECTION_RETRIEVAL_COUNT = 5
REFLECTION_PERIOD = 5
CHECK_REFLECTION_PERIOD = 5
CHECK_SATURATION_PEROID = 5
RESEARCH_GOALS = "experience in Vr chat, what activities they like doing in Vr chat and overall why do they value regarding VR chat?"
DEBATE_GOALS = "AI Agents should be included in VRChat in the future"

all_conversations = []

CSV_LOGGER = CSVLogger()

def filler(currentConversation):

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


def audio_conversation_input(CSV_LOGGER, FILENAME):
    start = time.perf_counter()
    listenAndRecordDirect(CSV_LOGGER, FILENAME)
    threading.Thread(target=fillerShort, args=()).start()
    end = time.perf_counter()
    audio_record_time = round(end - start, 2)
    CSV_LOGGER.set_enum(LogElements.TIME_FOR_INPUT, audio_record_time)

    start = time.perf_counter()
    currentConversation = getTextfromAudio(FILENAME)
    end = time.perf_counter()
    audio_to_text_time = round(end - start, 2)
    CSV_LOGGER.set_enum(LogElements.TIME_AUDIO_TO_TEXT, audio_to_text_time)
    threading.Thread(target=filler, args=(currentConversation,)).start()
    deleteAudioFile(FILENAME)
    return currentConversation


def startConversation(npc_name, currMode, agent_mode):
    global pastObservations
    global all_conversations

    if agent_mode == AGENT_MODE.NORMAL.value or agent_mode == AGENT_MODE.RESEARCH.value or agent_mode == AGENT_MODE.DEBATE.value:
        conversationalUser = input("Define the username you are acting as: ")
    elif agent_mode == AGENT_MODE.EVENT.value:
        conversationalUser = "User"
    baseObservation = fetchBaseDescription(npc_name)
    pastObservations = fetchPastRecords(conversationalUser)
    eventLoop = asyncio.get_event_loop()
    threadExecutor = ThreadPoolExecutor()

    if agent_mode == AGENT_MODE.NORMAL.value:
        STARTING_NOTIFICATION=f"Hi, {conversationalUser}. My Name is Ellma_AI, I'm your virtual chitchat friend here today. Let's dive into our conversation."
    elif agent_mode == AGENT_MODE.RESEARCH.value:
        STARTING_NOTIFICATION=f"Hi, {conversationalUser}. My Name is Ellma_AI, I'm your virtual interviewer here today. Today our topic is {RESEARCH_GOALS}.Let's dive into our conversation."
    elif agent_mode == AGENT_MODE.DEBATE.value:
        STARTING_NOTIFICATION = f"Hi, {conversationalUser}. My Name is Ellma_AI, I'm your virtual debator here today. Today our debate topic is {DEBATE_GOALS}.Let's dive into our conversation."
    elif agent_mode == AGENT_MODE.EVENT.value:
        STARTING_NOTIFICATION = f"Hi, there. My Name is Ellma_AI, I'm a virtual event publisher. Feel free to let me know if there is any event you want to hold or join. I can help you with it."
    openaiTTS.generateAudio(STARTING_NOTIFICATION, Virtual_MIC_Channel)
    VRC_OSCLib.actionChatbox(VRCclient, STARTING_NOTIFICATION)
    conversation_count = 0
    while True:
        push_conversation = True  # only push conversation if it is not a question
        current_conversation = ""
        is_question = False

        if currMode == CONVERSATION_MODE.TEXT.value:
            currentConversation = text_conversation_input(agent_mode, npc_name, conversationalUser, conversation_count)
        elif currMode == CONVERSATION_MODE.AUDIO.value:
            currentConversation = audio_conversation_input(CSV_LOGGER, FILENAME)
        CSV_LOGGER.set_enum(LogElements.MESSAGE, currentConversation)

        if currentConversation.lower() == "done":
            break

        if agent_mode != AGENT_MODE.EVENT.value:
            current_conversation += f"User: {currentConversation}. "
        elif agent_mode == AGENT_MODE.EVENT.value:
            is_question = is_question_function(currentConversation)
            print(f"Is question: {is_question}")
            if not is_question:
                current_conversation += f"{currentConversation}. "

        start = time.perf_counter()
        baseRetrieval, observationRetrieval = perform_observation_retrieval(agent_mode, currentConversation,
                                                                            baseObservation, pastObservations)
        end = time.perf_counter()

        retrieval_time = round(end - start, 2)
        CSV_LOGGER.set_enum(LogElements.TIME_RETRIEVAL, retrieval_time)
        if agent_mode == AGENT_MODE.NORMAL.value:
            important_observations = [data[1] for data in baseRetrieval + observationRetrieval]
        else:
            important_observations = [data[1] for data in observationRetrieval]
        CSV_LOGGER.set_enum(
            LogElements.IMPORTANT_OBSERVATIONS, "\n".join(
                important_observations)
        )
        # print(f"base retrieval: {baseRetrieval}")
        # print(f"observation retrieval: {observationRetrieval}")
        print(f"Important Observations: {important_observations}")

        if agent_mode == AGENT_MODE.NORMAL.value:
            important_scores = [round(data[0], 2) for data in baseRetrieval + observationRetrieval]
        else:
            important_scores = [round(data[0], 2) for data in observationRetrieval]
        CSV_LOGGER.set_enum(
            LogElements.IMPORTANT_SCORES, "\n".join(map(str, important_scores))
        )

        start = time.perf_counter()
        conversationPrompt = generate_conversation_helper(npc_name, conversationalUser, currentConversation,
                                                          important_observations, avatar_expressions, avatar_actions,
                                                          agent_mode, is_question=is_question)
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
                    openaiTTS.generateAudio(splitSentence, 9)
                    # tts.speech(splitSentence, "Joanna", 9)
                    VRC_OSCLib.actionChatbox(VRCclient, splitSentence)
                    splitSentence = ""  # Reset splitSentence
            except:
                break
        # npc_dialogues.append((conversationalUser, resultConversationString))
        # print(npc_dialogues)
        if splitSentence:
            # Additional actions for the remaining splitSentence
            openaiTTS.generateAudio(splitSentence, 9)
            # tts.speech(splitSentence, "Joanna", 9)
            VRC_OSCLib.actionChatbox(VRCclient, splitSentence)
            print(splitSentence, end="")
        CSV_LOGGER.set_enum(LogElements.NPC_RESPONSE, resultConversationString)
        CSV_LOGGER.set_enum(LogElements.TIME_FOR_RESPONSE, npc_response_time)
        threading.Thread(target=VRC_OSCLib.send_expression_command, args=(emotions,)).start()
        filtered_result = filter_conversation(resultConversationString)
        if agent_mode != AGENT_MODE.EVENT.value:
            current_conversation += f"{npc_name}: {filtered_result}.\n"

        print()

        CSV_LOGGER.write_to_csv(True)  # write all values to csv

        print(
            f"Time taken for the conversation generation by GPT : {npc_response_time}"
        )
        if push_conversation:
            eventLoop.run_in_executor(threadExecutor, generateObservationAndUpdateMemory, npc_name, conversationalUser,
                                      currentConversation, resultConversationString, current_conversation)

        all_conversations.append(current_conversation)

        conversation_count += 1
        if conversation_count != 1 and conversation_count % REFLECTION_PERIOD == 0 and agent_mode == AGENT_MODE.NORMAL.value:
            eventLoop.run_in_executor(threadExecutor, perform_reflection_logic, npc_name, conversationalUser,
                                      currentConversation, pastObservations)

        if conversation_count != 1 and conversation_count % CHECK_SATURATION_PEROID == 0 and perform_saturation_logic(
                npc_name, conversationalUser, all_conversations):
            threading.Thread(target=VRC_OSCLib.actionChatbox,
                             args=(VRCclient, "<Conversation ended due to saturation(Early Stopping)>.",)).start()
            print("Conversation ended due to saturation.")

            break


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
    # print(f"NPC reflection: {finalObservations}")
    update_reflection_db_and_past_obs(
        userName,
        conversationalUser,
        finalObservations
    )


# def perform_saturation_logic(
#         userName, conversationalUser, all_conversations
# ):
#     print("NPC in determinting saturation...\n")
#
#     response = generate_saturation_prompt(
#         userName,
#         conversationalUser,
#         pastConversations=all_conversations,
#     )
#     print(f"Saturation response: {response}")
#     if "True" in response:
#         return True
#     elif "False" in response:
#         return False


def generateObservationAndUpdateMemory(
        userName,
        conversationalUser,
        currentConversation,
        resultConversationString,
        npc_dialogues
):
    # # Time the function call and fetch the results.
    # startTime = time.perf_counter()
    # observationList = generateObservations(
    #     userName, conversationalUser, currentConversation, resultConversationString
    # )
    # observationList = observationList.split("\n")
    finalObservations = []
    finalObservations.append(npc_dialogues)
    # for observation in observationList:
    #     if len(observation) > 0:
    #         finalObservations.append(observation)

    # endTime = time.perf_counter()
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
    summirzation_response = perform_summurization_logic(npc_name, all_conversations)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"evaluations/Summary/summarization_response_{timestamp}.txt"
    write_to_file(summirzation_response, filename)
    # print(f"Summarization response: {summirzation_response}")
    client.close()