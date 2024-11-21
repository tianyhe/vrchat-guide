import os
from dotenv import load_dotenv
import re
load_dotenv()
import random
import VRC_OSCLib
import time
GPT4='gpt-4'
GPT35='gpt-3.5-turbo'
API_KEY=os.environ.get('API_KEY')

def generate_random_action(client):
    while(1):
        rand_action=random.randint(1, 8)
        if rand_action==1:
        #look left
            VRC_OSCLib.acitonLook_left(client, 2)
            print("random move--acitonLook_left")
        elif rand_action==2:
        # look right
            VRC_OSCLib.acitonLook_right(client,2)
            print("random move--acitonLook_right")
        elif rand_action==3:
        # walk forward
            VRC_OSCLib.acitonMove(client,"forward", 0.2 ,False)
            print("random move--acitonMove_forward")
        elif rand_action==4:
        # walk backward
            VRC_OSCLib.acitonMove(client, "backward", 0.2, False)
            print("random move--acitonMove_backward")
        elif rand_action==5:
        # walk left
            VRC_OSCLib.acitonMove(client, "left", 0.2, False)
            print("random move--acitonMove_left")
        elif rand_action == 6:
        # walk right
            VRC_OSCLib.acitonMove(client, "right", 0.2, False)
            print("random move--acitonMove_right")
        elif rand_action==7:
        # jump
            VRC_OSCLib.acitonJump(client)
            print("random move--jump")
        else:
            print("no movements")
        time.sleep(5)

def extract_emotions(text):
    # Find all occurrences of content within parentheses
    matches = re.findall(r'\((.*?)\)', text)
    return matches

def remove_emotions_from_string(conversation_string):
    # Replace patterns like (Smug, Dance) with an empty string
    cleaned_string = re.sub(r"\(.*?\)", "", conversation_string).strip()
    return cleaned_string