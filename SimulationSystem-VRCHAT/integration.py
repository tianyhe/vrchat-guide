from responseGenerator import *
import time
import asyncio
# from concurrent.futures import ThreadPoolExecutor
# from retrievalFunction import retrievalFunction
from audioRecorder import listenAndRecordDirect, deleteAudioFile
from csvLogger import CSVLogger, LogElements
# from collections import deque
# from avatar_data import avatar_action_map, avatar_expression_map, avatar_voice
import datetime
import os
from dotenv import load_dotenv
from collections import deque
from pymongo.mongo_client import MongoClient
from dialoge_helper import *
# from enums import CONVERSATION_MODE, AGENT_MODE, AVATAR_DATA
# from dialoge_helper import get_npc_name
import VRC_OSCLib
import argparse
from pythonosc import udp_client
import random
import fillerWords
from TTS import openaiTTS, audio_device
# from TTS import Polly
from STT import deepgramSTT
import controlexpression
import threading
from worksheets.agent import Agent
from worksheets.chat import generate_next_turn
from vrchat_guide.vrchatbot import (
    update_profile,
    add_event,
    prompt_dir,
    suql_knowledge,
    suql_parser,
)
# load_dotenv()


# CABLE-C Input
Virtual_MIC_Channel = audio_device.get_vbcable_devices_info().cable_c_input.id
#VRC client
parser = argparse.ArgumentParser()
parser.add_argument("--ip", default="127.0.0.1",
                        help="The ip of the OSC server")
parser.add_argument("--port", type=int, default=9000,
                        help="The port the OSC server is listening on")

parser.add_argument("--use_cable_d", action="store_true",
                    help="Use CABLE-D as the input device")
args = parser.parse_args()
# At the top of the file, after argument parsing
# if args.use_cable_d:
#     print("Using CABLE-D as input device")
#     Virtual_MIC_Channel = audio_device.get_vbcable_devices_info().cable_d_input.id
# else:
#     print("Using CABLE-C as input device")
#     Virtual_MIC_Channel = audio_device.get_vbcable_devices_info().cable_c_input.id

   

VRCclient = udp_client.SimpleUDPClient(args.ip, args.port)

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

def audio_conversation_input(CSV_LOGGER, FILENAME):
    print("inside audio_conversation_input")
    print("Starting audio recording on CABLE-D...")
    start = time.perf_counter()
    listenAndRecordDirect(CSV_LOGGER, FILENAME)
    print("Audio recording complete, processing...")
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

def bot_speak(text, split=False):
    if split:
        for text in text.split("|"):
            openaiTTS.generateAudio(text, Virtual_MIC_Channel)
            VRC_OSCLib.actionChatbox(VRCclient, text)
    else:
        openaiTTS.generateAudio(text, Virtual_MIC_Channel)
        VRC_OSCLib.actionChatbox(VRCclient, text)

def get_input():
    print("inside get_input")
    current_text = audio_conversation_input(CSV_LOGGER, FILENAME)
    return current_text

# async def main():
#     bot = Agent(
#         botname="VRChatBot",
#         description="VRChat assistant helping with events and calendar",
#         prompt_dir=prompt_dir,
#         starting_prompt="Hello! I'm your VRChat Guide. How can I help you today?",
#         args={},
#         api=[update_profile, add_event],
#         knowledge_base=suql_knowledge,
#         knowledge_parser=suql_parser,
#     ).load_from_gsheet(
#         gsheet_id="1aLyf6kkOpKYTrnvI92kHdLVip1ENCEW5aTuoSZWy2fU"
#     )

#     # Initialize conversation with starting prompt
#     bot_speak(bot.starting_prompt)

#     while True:
#         # Get user input through audio
#         user_input = get_input()
#         print(f"User said: {user_input}")  # Add logging to verify input

#         # Generate and speak response
#         response = await generate_next_turn_cl(user_input, bot)
#         print(f"Bot responding: {response}")  # Add logging to verify output
#         bot_speak(response)

async def main():
    bot = Agent(
        botname="VRChatBot",
        description="VRChat assistant helping with events and calendar",
        prompt_dir=prompt_dir,
        starting_prompt="Hello! I'm your VRChat Guide. How can I help you today?",
        args={},
        api=[update_profile, add_event],
        knowledge_base=suql_knowledge,
        knowledge_parser=suql_parser,
    ).load_from_gsheet(
        gsheet_id="1aLyf6kkOpKYTrnvI92kHdLVip1ENCEW5aTuoSZWy2fU"
    )

    # Initialize conversation with both text and voice
    print("Starting conversation...")
    openaiTTS.generateAudio(bot.starting_prompt, Virtual_MIC_Channel)
    VRC_OSCLib.actionChatbox(VRCclient, bot.starting_prompt)

    while True:
        print("Listening for input...")
        user_input = get_input()
        print(f"User said: {user_input}")

        # Generate response
        await generate_next_turn(user_input, bot)
        response = bot.dlg_history[-1].system_response
        print(f"Bot responding: {response}")

        # Send both voice and text response
        openaiTTS.generateAudio(response, Virtual_MIC_Channel)
        VRC_OSCLib.actionChatbox(VRCclient, response)


if __name__ == "__main__":
    asyncio.run(main())
    # username = None
    # while True:
    #     # Ask the user if they want to login or create a new profile
    #     if username is None:
    #         bot_speak("Hello, I'm your VRChat onboarding guide created by Eddie. Would you like to create a new VRChat profile or login existing one? You can just say I want to login with your username.")
    #         user_input = get_input()
    #         if user_wants_login(user_input):
    #             username = extract_username(user_input)
    #             if not os.path.exists(f"{username}_profile.json"):
    #                 bot_speak(f"No profile found for {username}.")
    #                 username = None
    #                 continue
    #         elif user_wants_create_profile(user_input):
    #             username = create_new_profile()
    #         else:
    #             bot_speak("Sorry, I didn't understand. Please try again.")
    #             continue
    #     else:
    #         # Ask the user what they want to do like modify their profile or have a world recommendation, give the prompt
    #         bot_speak(f"Hello {username}, What would you like to do next? Like modify your profile, logout or have a world or event recommendation?")
    #         user_input = get_input()
    #         if user_wants_to_change_profile(user_input):
    #             modify_existing_profile(username)
    #         if user_wants_logout(user_input):
    #             username = None
    #             bot_speak("You have been logged out.")
    #             continue
    #         elif user_wants_show_profile(user_input):
    #             review_data(username)
    #             continue
    #         elif user_wants_world_recommendation(user_input):
    #             recommendations = get_world_recommendation(f"{username}_profile.json", "filtered_worlds_cleaned_new.json")
    #             found = False
    #             for recommendation in recommendations:
    #                 bot_speak(f"World Name: {recommendation['world_name']}")
    #                 bot_speak(recommendation["description"], split=True)
    #                 bot_speak("Would you like to visit this world?")
    #                 user_input = get_input()
    #                 if extract_yes_no(user_input) == "yes":
    #                     bot_speak(f"Please open world {recommendation['world_name']} in VRChat. If you have any more questions, stay here to ask.")
    #                     found = True
    #                     break
    #             if not found:
    #                 bot_speak("It seems there is no world recommendation for you at the moment. You can modify your profile to get better recommendations.")
    #             continue
    #         elif user_wants_events_recommendation(user_input):
    #             recommendations = get_event_recommendation(f"{username}_profile.json")
    #             found = False
    #             for recommendation in recommendations:
    #                 bot_speak(f"Event Name: {recommendation['event_name']}")
    #                 bot_speak(recommendation["description"], split=True)
    #                 bot_speak("Would you like to attend this event?")
    #                 user_input = get_input()
    #                 if extract_yes_no(user_input) == "yes":
    #                     send_email(recommendation["htmlLink"], recommendation["event_name"], username)
    #                     bot_speak(f"Please join the event {recommendation['event_name']} in VRChat. If you have any more questions, stay here to ask.")
    #                     found = True
    #                     break
    #             if not found:
    #                 bot_speak("It seems there is no event recommendation for you at the moment. You can modify your profile to get better recommendations.")
    #             continue
    #         else:
    #             answer = answer_vrchat_question(user_input)
    #             bot_speak(answer)
