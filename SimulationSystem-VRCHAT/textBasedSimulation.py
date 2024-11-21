import time
import os
import datetime
import asyncio
import controlexpression
import auto_correct_model
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from collections import deque
from dotenv import load_dotenv
from retrievalFunction import retrievalFunction
from pymongo.mongo_client import MongoClient
from audioRecorder import listenAndRecordDirect, deleteAudioFile
from responseGenerator01 import (
    generateInitialObservations,
    generateObservations,
    generateConversation,
    getTextfromAudio,
)
import VRC_OSCLib
import argparse
from pythonosc import udp_client
from csvLogger import CSVLogger, LogElements
import easyocr1
from TTS import openaiTTS
import random
import fillerWords
from TTS import Polly
from STT import deepgramSTT
# Define list of expressions and actions for GPT and allow it to pick one

load_dotenv()
# test avatar list
# Avatar_list=["Clarla","Sakura0319","chmx2023"]
# Constants
DATABASE_NAME = "LLMDatabase"
DATABASE_URL = os.environ.get("DATABASE_URL")
COLLECTION_USERS = "Users"
COLLECTION_MEMORY_OBJECTS = "TestMemory"
# Basic objects for the Database.
client= MongoClient(DATABASE_URL)
LLMdatabase= client[DATABASE_NAME]
userCollection= LLMdatabase[COLLECTION_USERS]
memoryObjectCollection=LLMdatabase[COLLECTION_MEMORY_OBJECTS]

Context=[]
RETRIEVAL_COUNT = 5
FILENAME = "./speech/current_conversation.wav"
CSV_LOGGER = CSVLogger()
tts = Polly.Polly()
#client
parser = argparse.ArgumentParser()
parser.add_argument("--ip", default="127.0.0.1",
                        help="The ip of the OSC server")
parser.add_argument("--port", type=int, default=9000,
                        help="The port the OSC server is listening on")
args = parser.parse_args()
VRCclient = udp_client.SimpleUDPClient(args.ip, args.port)

class CONVERSATION_MODE(Enum):
    TEXT = 1
    AUDIO = 2

class INPUTUSERNAME_MODE(Enum):
    INPUT = 1
    AUTODETECT = 2
# Basic objects for the Database.

def add_to_queue(ocr_queue,ocr_text):
    ocr_queue.append(ocr_text)

# Fetch the base description once.
def fetchBaseDescription(userName: str):
    return deque(
        memoryObjectCollection.find(
            {"Username": userName, "Conversation with User": "Base Description"}
        ),
    )


# fetch the past records once.
def fetchPastRecords(userName: str):
    fetchQuery = {
        "$or": [{"Username": userName}, {"Conversation with User": userName}],
        "Conversation with User": {"$ne": "Base Description"},
    }
    return deque(
        memoryObjectCollection.find(fetchQuery).sort("_id", -1).limit(50), maxlen=50
    )


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


def updateMemoryCollection(
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
    if len(pastObservations) > 15:
        pastObservations.pop()
    pastObservations.appendleft(memoryObjectData)


def getBaseDescription():
    description = ""
    while True:
        currLine = input(
            "Please enter a relevant description about your character. Type done to complete the description \n"
        )
        if currLine.lower() == "done":
            break
        description += f"{currLine}\n"
    return description

def filler(currentConversation, round):
    if round==0:
        selected_filler_key = random.choice(list(fillerWords.fillersG.keys()))
        VRC_OSCLib.actionChatbox(VRCclient, fillerWords.fillersG[selected_filler_key])
        openaiTTS.read_audio_file("TTS/fillerWord/" + selected_filler_key + ".ogg", 9)
    else:
        if "?" in currentConversation and len(currentConversation)>40:
            selected_filler_key = random.choice(list(fillerWords.fillersQ.keys()))
            VRC_OSCLib.actionChatbox(VRCclient, fillerWords.fillersQ[selected_filler_key])
            openaiTTS.read_audio_file("TTS/fillerWord/"+selected_filler_key+".ogg", 9)

        else:
            selected_filler_key = random.choice(list(fillerWords.fillers.keys()))
            VRC_OSCLib.actionChatbox(VRCclient, fillerWords.fillers[selected_filler_key])
            openaiTTS.read_audio_file("TTS/fillerWord/"+selected_filler_key+".ogg", 9)

def fillerShort():
    selected_filler_key = random.choice(list(fillerWords.fillersS.values()))
    VRC_OSCLib.actionChatbox(VRCclient, selected_filler_key)
    openaiTTS.read_audio_file("TTS/fillerWord/Pollyfiller/"+selected_filler_key+".ogg", 9)


def startConversation(userName, currMode, usernameMode):
    global pastObservations
    round=0
    if usernameMode ==INPUTUSERNAME_MODE.INPUT.value:
        conversationalUser = input("Define the username you are acting as: ")
    elif usernameMode ==INPUTUSERNAME_MODE.AUTODETECT.value:
        while(1):
            print("Detecting User Name...\n")
            OCRtext = easyocr1.run_image_processing("VRChat", ["en"])
            correct = input(
                f"Detected UserName--{OCRtext}\nPlease select the following :\n1. Yes\n2. No\n "
            )
            if correct=="1":
                conversationalUser=OCRtext
                break
    baseObservation = fetchBaseDescription(userName)
    pastObservations = fetchPastRecords(userName)
    eventLoop = asyncio.get_event_loop()
    threadExecutor = ThreadPoolExecutor()
    while True:
        # thread = threading.Thread(target=controlexpression.generate_random_action(VRCclient))
        # thread.start()
        # controlexpression.generate_random_action(VRCclient)
        if currMode == CONVERSATION_MODE.TEXT.value:
            start = time.perf_counter()
            currentConversation = input(
                f"Talk with {userName}, You are {conversationalUser}. Have a discussion! "
            )
            end = time.perf_counter()
            text_input_time = round(end - start, 2)
            CSV_LOGGER.set_enum(LogElements.TIME_FOR_INPUT, text_input_time)
            CSV_LOGGER.set_enum(LogElements.TIME_AUDIO_TO_TEXT, 0)
        else:
            start = time.perf_counter()
            listenAndRecordDirect(CSV_LOGGER, FILENAME)
            # fillerShort()
            # currentConversation = getTextfromAudio(FILENAME)
            currentConversation=deepgramSTT.transTTDeepgram()
            end = time.perf_counter()
            audio_to_text_time = round(end - start, 2)
            CSV_LOGGER.set_enum(LogElements.TIME_FOR_INPUT, audio_to_text_time)
            CSV_LOGGER.set_enum(LogElements.MESSAGE, currentConversation)
            print(currentConversation)
            # filler(currentConversation)

        start = time.perf_counter()
        baseRetrieval = retrievalFunction(
            currentConversation,
            baseObservation,
            RETRIEVAL_COUNT,
            isBaseDescription=True,
        )
        observationRetrieval = retrievalFunction(
            currentConversation,
            pastObservations,
            RETRIEVAL_COUNT,
            isBaseDescription=False,
        )
        end = time.perf_counter()
        retrieval_time = round(end - start, 2)
        CSV_LOGGER.set_enum(LogElements.TIME_RETRIEVAL, retrieval_time)

        important_observations = [
            data[1] for data in baseRetrieval + observationRetrieval
        ]

        CSV_LOGGER.set_enum(
            LogElements.IMPORTANT_OBSERVATIONS, "\n".join(important_observations)
        )
        important_scores = [
            round(data[0], 2) for data in baseRetrieval + observationRetrieval
        ]

        CSV_LOGGER.set_enum(
            LogElements.IMPORTANT_SCORES, "\n".join(map(str, important_scores))
        )
        start = time.perf_counter()
        conversationPrompt = generateConversation(
            userName,
            conversationalUser,
            currentConversation,
            important_observations,
        )
        end = time.perf_counter()
        npc_response_time = round(end - start, 2)
        print(f"{userName} :")
        resultConversationString = ""
        splitSentence = ""
        count=0
        # start = time.perf_counter()
        for conversation in conversationPrompt:
            try:
                currText = conversation.choices[0].delta.content

                # Always add the current text to resultConversationString
                resultConversationString += currText
                splitSentence += currText

                # Check for specific punctuation marks in splitSentence
                if any(punct in currText for punct in ['.', '?', '!']):
                    if count==0:
                        emotions = controlexpression.extract_emotions(splitSentence)
                        splitSentence = controlexpression.remove_emotions_from_string(splitSentence)
                        count+=1
                        print(splitSentence, end="")
                    print(splitSentence, end="")
                    # Additional actions
                    # openaiTTS.generateAudio(splitSentence, 9)
                    tts.speech(splitSentence, "Joanna", 8)
                    VRC_OSCLib.actionChatbox(VRCclient, splitSentence)
                    splitSentence = ""  # Reset splitSentence
            except:
                break

        if splitSentence:
            # Additional actions for the remaining splitSentence
            # openaiTTS.generateAudio(splitSentence, 9)
            tts.speech(splitSentence, "Joanna", 8)
            VRC_OSCLib.actionChatbox(VRCclient, splitSentence)
            print(splitSentence, end="")

        # end = time.perf_counter()
        # TTS_response_time = round(end - start, 2)
        # CSV_LOGGER.set_enum(LogElements.TIME_FOR_TTS, TTS_response_time)
        CSV_LOGGER.set_enum(LogElements.NPC_RESPONSE, resultConversationString)
        CSV_LOGGER.set_enum(LogElements.TIME_FOR_RESPONSE, npc_response_time)
        CSV_LOGGER.write_to_csv(True)
        print(resultConversationString)
        print(
            f"Time taken for the conversation generation by GPT : {npc_response_time}"
        )
        # emotions = controlexpression.extract_emotions(resultConversationString)
        # result = controlexpression.remove_emotions_from_string(resultConversationString)
        # print(emotions)
        # print(result)
        print()
        round+=1
        #texttospeech time
        starttime = time.perf_counter()
        # openaiTTS.generateAudio(result, 9)
        # VRC_OSCLib.actionChatbox(VRCclient, result)
        endtime = time.perf_counter()
        retrieval_time2 = round(endtime - starttime, 2)
        CSV_LOGGER.set_enum(LogElements.TIME_FOR_TTS, retrieval_time2)
        starttime = time.perf_counter()
        VRC_OSCLib.send_expression_command(emotions)
        endtime = time.perf_counter()
        retrieval_time1 = round(endtime - starttime , 2)
        CSV_LOGGER.set_enum(LogElements.TIME_FOR_CONTROLEXP, retrieval_time1)
        deleteAudioFile(FILENAME)
        eventLoop.run_in_executor(
            threadExecutor,
            generateObservationAndUpdateMemory,
            userName,
            conversationalUser,
            currentConversation,
            resultConversationString,
        )


def generateObservationAndUpdateMemory(
    userName, conversationalUser, currentConversation, resultConversationString
):
    
    # Time the function call and fetch the results.
    startTime = time.time()
    observationList = generateObservations(
        userName, conversationalUser, currentConversation, resultConversationString
    )
    observationList = observationList.split("\n")
    finalObservations = []
    for observation in observationList:
        if len(observation) > 0:
            finalObservations.append(observation)

    endTime = time.time()
    """
    print(
        f"Time taken for the observation generation by GPT : {endTime-startTime:.2f} "
    )
    """

    updateMemoryCollection(userName, conversationalUser, finalObservations)


def setConversationMode():
    while True:
        currMode = input("Please select the following :\n1. Text Mode\n2. Audio Mode\n")
        if currMode == "1":
            return CONVERSATION_MODE.TEXT.value
        elif currMode == "2":
            return CONVERSATION_MODE.AUDIO.value
        else:
            print("Invalid input, please select appropriate options")



if __name__ == "__main__":
    pastObservations = deque()
    # Get username.
    userName = input("Please enter the username of character: ")

    # Check for existing user.
    existingUser = userCollection.find_one({"Username": userName})

    if existingUser:
        print(f"Welcome back! {userName} \nContinue where you left off")
    else:
        # Collect the description details.
        description = getBaseDescription()

        # Insert the userData to the Users collection.
        userData = {"Username": userName, "Description": description}
        userCollection.insert_one(userData)

        # Time the function call and fetch the results.
        startTime = time.time()
        observationList = generateInitialObservations(userName, description).split("\n")
        endTime = time.time()
        print(
            f"Time taken for the observation generation by GPT : {endTime-startTime:.2f} "
        )

        # Generate the memory object data and push it to the memory objects collection.
        updateBaseDescription(userName, observationList)
        print("User created successfully!")
    NameMode = input("Please select one the following ways of detecting User Name:\n1. Manually Input\n2. Auto detect\n")
    if NameMode == "1":
        currMode = setConversationMode()
        startConversation(userName, currMode,1)
    elif NameMode == "2":
        currMode = setConversationMode()
        startConversation(userName, currMode,2)
    else:
        print("Invalid input, please select appropriate options")

    client.close()
