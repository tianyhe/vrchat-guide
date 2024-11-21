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
from dialoge_helper import *
from enums import CONVERSATION_MODE, AGENT_MODE, AVATAR_DATA
from dialoge_helper import get_npc_name
import VRC_OSCLib
import argparse
from pythonosc import udp_client
import random
import fillerWords
from TTS import openaiTTS, audio_device
from TTS import Polly
from STT import deepgramSTT
import controlexpression
import threading
load_dotenv()
FILENAME = "./speech/current_conversation.wav"

# CABLE-C Input
Virtual_MIC_Channel = audio_device.get_vbcable_devices_info().cable_c_input.id

CSV_LOGGER = CSVLogger()

#VRC client
parser = argparse.ArgumentParser()
parser.add_argument("--ip", default="127.0.0.1",
                        help="The ip of the OSC server")
parser.add_argument("--port", type=int, default=9000,
                        help="The port the OSC server is listening on")

parser.add_argument("--use_cable_d", action="store_true",
                    help="Use CABLE-D as the input device")
args = parser.parse_args()
VRCclient = udp_client.SimpleUDPClient(args.ip, args.port)
load_dotenv()

# Constants
DATABASE_NAME = "LLMDatabase"
DATABASE_URL = os.environ.get("DATABASE_URL")
COLLECTION_USERS = "NPC Avatars"
COLLECTION_MEMORY_OBJECTS = "ev018"

MAX_DEQUE_LENGTH = 50

# Basic objects for the Database.
client = MongoClient(DATABASE_URL)
LLMdatabase = client[DATABASE_NAME]
userCollection = LLMdatabase[COLLECTION_USERS]
memoryObjectCollection = LLMdatabase[COLLECTION_MEMORY_OBJECTS]

REFLECTION_RETRIEVAL_COUNT = 5
CHECK_REFLECTION_PERIOD = 5
CHECK_SATURATION_PEROID = 5
FILENAME = "./speech/current_conversation.wav"

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

def text_conversation_input(agent_mode, userName, conversationalUser, question_list, conversation_count):
    start = time.perf_counter()
    if agent_mode == AGENT_MODE.RESEARCH.value:
        currentConversation = input(
            f"Talks with {userName}, You are {conversationalUser}. Talk about {RESEARCH_GOALS}! "
        )
    elif agent_mode == AGENT_MODE.PREDEFINED_RESEARCH.value:
        currentConversation = input(
            f"{question_list[conversation_count]} "
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
    currentConversation = getTextfromAudio_whisper_1(FILENAME)
    end = time.perf_counter()
    audio_to_text_time = round(end - start, 2)
    CSV_LOGGER.set_enum(LogElements.TIME_AUDIO_TO_TEXT, audio_to_text_time)
    threading.Thread(target=filler, args=(currentConversation,)).start()
    deleteAudioFile(FILENAME)
    return currentConversation


def startConversation(npc_name, currMode, agent_mode):
    global pastObservations
    global all_conversations

    if agent_mode == AGENT_MODE.EVENT.value:
        conversationalUser = "User"
    else:
        conversationalUser = input("Define the username you are acting as: ")
    baseObservation = fetchBaseDescription(npc_name)
    pastObservations = fetchPastRecords(conversationalUser)
    eventLoop = asyncio.get_event_loop()
    threadExecutor = ThreadPoolExecutor()

    if agent_mode == AGENT_MODE.NORMAL.value:
        STARTING_NOTIFICATION=f"Hi, {conversationalUser}. My Name is Ellma_AI, I'm your virtual chitchat friend here today. Let's dive into our conversation."
    elif agent_mode == AGENT_MODE.RESEARCH.value or AGENT_MODE.PREDEFINED_RESEARCH.value:
        STARTING_NOTIFICATION=f"Hi, {conversationalUser}. My Name is Ellma_AI, I'm your virtual interviewer here today. Today our topic is {RESEARCH_GOALS}.Let's dive into our conversation."
    elif agent_mode == AGENT_MODE.DEBATE.value:
        STARTING_NOTIFICATION = f"Hi, {conversationalUser}. My Name is Ellma_AI, I'm your virtual debator here today. Today our debate topic is {DEBATE_GOALS}.Let's dive into our conversation."
    elif agent_mode == AGENT_MODE.EVENT.value:
        STARTING_NOTIFICATION = f"Hi, there. My Name is Ellma_AI, I'm a virtual event publisher. Feel free to let me know if there is any event you want to hold or join. I can help you with it."
    openaiTTS.generateAudio(STARTING_NOTIFICATION, Virtual_MIC_Channel)
    VRC_OSCLib.actionChatbox(VRCclient, STARTING_NOTIFICATION)

    conversation_count = 0
    question_list = []
    if agent_mode == AGENT_MODE.PREDEFINED_RESEARCH.value:
        question_list = generate_interview_questions(
            RESEARCH_GOALS, number_of_questions=INTERVIEW_ROUNDS,
        ).split("\n")
        question_list = remove_numbers(question_list)
    print(f"question_list: {question_list}")

    print(f"Starting conversation with {npc_name} as {conversationalUser}...\n")

    while True:
        current_conversation = ""
        is_question_event_agent = False

        if currMode == CONVERSATION_MODE.TEXT.value:
            currentConversation = text_conversation_input(agent_mode, npc_name, conversationalUser, question_list,
                                                          conversation_count)
        elif currMode == CONVERSATION_MODE.AUDIO.value:
            currentConversation = audio_conversation_input(CSV_LOGGER, FILENAME)
        CSV_LOGGER.set_enum(LogElements.MESSAGE, currentConversation)

        if currentConversation.lower() == "done":
            break

        if agent_mode != AGENT_MODE.EVENT.value:
            current_conversation += f"User: {currentConversation}. "
        elif agent_mode == AGENT_MODE.EVENT.value:
            is_question_event_agent = is_question_function(currentConversation)
            if not is_question_event_agent:
                current_conversation += f"{currentConversation}. "

        baseRetrieval, observationRetrieval, retrieval_time = perform_observation_retrieval(
            agent_mode, currentConversation, baseObservation, pastObservations
        )
        CSV_LOGGER.set_enum(LogElements.TIME_RETRIEVAL, retrieval_time)

        important_observations = select_important_observations(agent_mode, baseRetrieval, observationRetrieval)
        # print(f"Important Observations: {important_observations}")
        CSV_LOGGER.set_enum(LogElements.IMPORTANT_OBSERVATIONS, "\n".join(important_observations))
        important_scores = calculate_important_scores(agent_mode, baseRetrieval, observationRetrieval)
        CSV_LOGGER.set_enum(LogElements.IMPORTANT_SCORES, "\n".join(map(str, important_scores)))
        splitSentence = ""
        count = 0
        emotions=""
        if agent_mode == AGENT_MODE.PREDEFINED_RESEARCH.value:
            resultConversationString = question_list[conversation_count]
            for currText in resultConversationString:
                try:
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

            # CSV_LOGGER.set_enum(LogElements.TIME_FOR_RESPONSE, npc_response_time)
            filtered_result = filter_conversation(resultConversationString)
        else:
            start = time.perf_counter()
            conversationPrompt = generate_conversation_helper(npc_name, conversationalUser, currentConversation,
                                                              important_observations, avatar_expressions,
                                                              avatar_actions, agent_mode,
                                                              is_question=is_question_event_agent, )
            end = time.perf_counter()
            npc_response_time = round(end - start, 2)

            print(f"{npc_name} :")
            resultConversationString = ""
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

            CSV_LOGGER.set_enum(LogElements.TIME_FOR_RESPONSE, npc_response_time)
            filtered_result = filter_conversation(resultConversationString)
            if agent_mode != AGENT_MODE.EVENT.value:
                current_conversation += f"NPC: {filtered_result}.\n"
            print(f"Time taken for the conversation generation by GPT : {npc_response_time}")
        CSV_LOGGER.set_enum(LogElements.NPC_RESPONSE, resultConversationString)

        # npc_dialogues.append((conversationalUser, resultConversationString))
        # print(npc_dialogues)
        if splitSentence:
            # Additional actions for the remaining splitSentence
            openaiTTS.generateAudio(splitSentence, Virtual_MIC_Channel)
            # tts.speech(splitSentence, "Joanna", 9)
            VRC_OSCLib.actionChatbox(VRCclient, splitSentence)
            print(splitSentence, end="")
        CSV_LOGGER.set_enum(LogElements.NPC_RESPONSE, resultConversationString)
        start = time.perf_counter()
        threading.Thread(target=VRC_OSCLib.send_expression_command, args=(emotions,)).start()
        end = time.perf_counter()
        npc_response_time=end-start
        CSV_LOGGER.set_enum(LogElements.TIME_FOR_RESPONSE, npc_response_time)
        filtered_result = filter_conversation(resultConversationString)

        start = time.perf_counter()
        if not is_question_event_agent:
            eventLoop.run_in_executor(threadExecutor, generateObservationAndUpdateMemory, npc_name, conversationalUser,
                                      currentConversation, resultConversationString, current_conversation)
        end = time.perf_counter()
        generate_observation_time = round(end - start, 2)
        CSV_LOGGER.set_enum(LogElements.TIME_FOR_GENERATE_OBS, generate_observation_time)
        all_conversations.append(current_conversation)

        CSV_LOGGER.write_to_csv(True)  # write all values to csv

        conversation_count += 1

        if conversation_count != 1 and conversation_count % CHECK_REFLECTION_PERIOD == 0 and agent_mode == AGENT_MODE.NORMAL.value:
            start = time.perf_counter()
            eventLoop.run_in_executor(threadExecutor, perform_reflection_logic, npc_name, conversationalUser,
                                      currentConversation, pastObservations)
            end = time.perf_counter()
            reflection_time = round(end - start, 2)
            CSV_LOGGER.set_enum(LogElements.TIME_FOR_REFLECTION, reflection_time)

        if conversation_count != 1 and conversation_count % CHECK_SATURATION_PEROID == 0 and perform_saturation_logic(
                npc_name, conversationalUser, all_conversations):
            print("Conversation ended due to saturation.")
            break

        if conversation_count == INTERVIEW_ROUNDS and agent_mode == AGENT_MODE.PREDEFINED_RESEARCH.value:
            print("Conversation ended due to interview rounds.")
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
        is_only_recency=True,
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
    update_Memory_Collection_and_past_obs(
        userName, conversationalUser, finalObservations)


if __name__ == "__main__":
    currMode = setConversationMode()
    agent_mode = set_agent_mode()

    pastObservations = deque()
    npc_name = get_npc_name(agent_mode)

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