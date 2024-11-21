# Copyright (c) 2013 Iris
# Released under the MIT license
# https://opensource.org/licenses/mit-license.php

# Request "pythonosc" https://pypi.org/project/python-osc/

# OSC Imput Event Name => https://docs.vrchat.com/v2022.1.1/docs/osc-as-input-controller
import sys
import os
sys.path.append(os.path.abspath("../python-osc"))
import time
from pythonosc import udp_client
from pythonosc.osc_message_builder import OscMessageBuilder
from pythonosc.osc_bundle_builder import OscBundleBuilder
from unidecode import unidecode
from pythonosc import osc_bundle_builder
from pythonosc import osc_message_builder
from pythonosc import udp_client
import threading
import queue
import time
import argparse
import ast
import controlexpression
import string
# Variables and locks for thread safety and message queuing
send_message_lock = threading.Lock()
osc_queue = queue.Queue()
last_message_sent_time = 0
stop_flag = False
thread = None
min_time_between_messages = 1.5
# Mapping of expressions to data values
expression_data_mapping = {
    "Facial Expression": {
        "Happy": 2,
        "Tease": 5,
        "Wink": 4,
        "Confused": 3,
        "Sad": 6,
        "Angry": 1
    },
    "Body Expression (Emotes)": {
        "Wave Hands": 1,
        "Clap": 2,
        "Point": 3,
        "Cheer": 4,
        "Dance": 5,
        "Backflip": 6,
        "Sadness": 7
    }
}



# Dummy function to simulate AV3_SetInt, remove this in your actual code
def AV3_SetInt(**kwargs):
    print(f"AV3_SetInt called with parameters: {kwargs}")


def send_expression_command(expression, IP='127.0.0.1', PORT=9000):
    # Check if the expression is a list, and then extract the string
    if isinstance(expression, list) and len(expression) > 0:
        expression = expression[0]

    # Split the string by comma to get the individual expressions
    words = [word.strip() for word in expression.split(',')]

    for le in words:
        le = le.lower()
        found = False
        for expression_type, expressions in expression_data_mapping.items():
            # Convert dictionary keys to lowercase for matching
            lowercase_expressions = {k.lower(): v for k, v in expressions.items()}
            if le in lowercase_expressions:
                data_value = lowercase_expressions[le]
                parameter_value = "F" if expression_type == "Facial Expression" else "VRCEmote"
                AV3_SetInt(data=data_value, Parameter=parameter_value, IP=IP, PORT=PORT)
                print(f'Command sent for expression: {le} with data value: {data_value}')
                found = True
                time.sleep(3)
                AV3_SetInt(data=0, Parameter=parameter_value, IP=IP, PORT=PORT)
                break  # Exit the loop once a match is found

        if not found:
            print(f'Invalid expression: {le}')


def AV3_SetInt(data=0, Parameter="example", IP='127.0.0.1', PORT=9000):
    Int(data, "/avatar/parameters/" + Parameter, IP, PORT)


def AV3_SetFloat(data=0.0, Parameter="example", IP='127.0.0.1', PORT=9000):
    Float(data, "/avatar/parameters/" + Parameter, IP, PORT)


def AV3_SetBool(data=False, Parameter="example", IP='127.0.0.1', PORT=9000):
    Bool(data, "/avatar/parameters/" + Parameter, IP, PORT)


def Control_Push(Button="example", IP='127.0.0.1', PORT=9000):
    Buttons("/input/" + Button, IP, PORT)


def Control_Joystick(data=0.0, axis="example", IP='127.0.0.1', PORT=9000):
    Float(data, "/input/" + axis, IP, PORT)


def RemoveNonASCII(data):
    new_val = data.encode("ascii", "ignore")
    return new_val.decode()


# Button
def Buttons(address="/input/example", IP='127.0.0.1', PORT=9000):
    # OSC Bild
    client = udp_client.UDPClient(IP, PORT)
    msg = OscMessageBuilder(address=address)
    msg.add_arg(1)
    m = msg.build()

    msgb = OscMessageBuilder(address=address)
    msgb.add_arg(0)
    mb = msgb.build()

    # OSC Send
    client.send(m)
    time.sleep(0.1)
    client.send(mb)


# Int
def Int(data=0, address="/input/example", IP='127.0.0.1', PORT=9000):
    senddata = int(data)
    # OSC Bild
    client = udp_client.UDPClient(IP, PORT)
    msg = OscMessageBuilder(address=address)
    msg.add_arg(senddata)
    m = msg.build()

    # OSC Send
    client.send(m)


# Float
def Float(data=0.0, address="/input/example", IP='127.0.0.1', PORT=9000):
    senddata = float(data)
    # OSC Bild
    client = udp_client.UDPClient(IP, PORT)
    msg = OscMessageBuilder(address=address)
    msg.add_arg(senddata)
    m = msg.build()

    # OSC Send
    client.send(m)


# Bool
def Bool(data=False, address="/input/Jump", IP='127.0.0.1', PORT=9000):
    # OSC Bild
    client = udp_client.UDPClient(IP, PORT)
    msg = OscMessageBuilder(address=address)
    msg.add_arg(data)
    m = msg.build()

    # OSC Send
    client.send(m)


def set_min_time_between_messages(time_in_seconds):
    global min_time_between_messages
    min_time_between_messages = time_in_seconds


def _send_osc_message():
    global last_message_sent_time, min_time_between_messages
    print("min_time_between_messages: " + str(min_time_between_messages))
    while True:
        try:
            # Wait for a message to be available in the queue. This will block until a message is available.
            message_data = osc_queue.get()

            # Discard all but the latest message in the queue.
            while not osc_queue.empty():
                message_data = osc_queue.get()

            current_time = time.time()
            time_since_last_message = current_time - last_message_sent_time
            if time_since_last_message < min_time_between_messages:
                time_to_wait = min_time_between_messages - time_since_last_message
                time.sleep(time_to_wait)

            # Send the actual OSC message here using the original Chat function
            _direct_osc_send(**message_data)

            last_message_sent_time = time.time()

        except Exception as e:
            # This can be useful for debugging any exceptions that might occur
            print(f"Error in OSC sender thread: {e}")
            time.sleep(0.1)


# Start the OSC message sender thread
osc_sender_thread = threading.Thread(target=_send_osc_message)
osc_sender_thread.daemon = True
osc_sender_thread.start()


# OSC Send Command
def Message(data="example", address="/example", IP='127.0.0.1', PORT=9000):
    # OSC Bild
    client = udp_client.UDPClient(IP, PORT)
    msg = OscMessageBuilder(address=address)
    msg.add_arg(data)
    m = msg.build()

    # OSC Send
    client.send(m)


def Chat(data="example", send=True, nofify=True, address="/chatbox/input", IP='127.0.0.1', PORT=9000, convert_ascii=False):
    with send_message_lock:
        # Enqueue the message for sending
        osc_queue.put({
            "data": data,
            "send": send,
            "nofify": nofify,
            "address": address,
            "IP": IP,
            "PORT": PORT,
            "convert_ascii": convert_ascii
        })


# OSC Send Chat
def _direct_osc_send(data="example", send=True, nofify=True, address="/chatbox/input", IP='127.0.0.1', PORT=9000, convert_ascii=False):
    # OSC Bild
    client = udp_client.UDPClient(IP, PORT)

    msg = OscMessageBuilder(address=address)
    if convert_ascii:
        msg.add_arg(unidecode(data))
    else:
        msg.add_arg(data)
    msg.add_arg(send)
    msg.add_arg(nofify)
    m = msg.build()

    # OSC Send
    client.send(m)


def count_utf16_code_units(s):
    return len(s.encode('utf-16le')) // 2


def split_words(text, chunk_size):
    words = text.split()
    chunks = []
    current_chunk = ""

    for i, word in enumerate(words):
        # If a word is longer than the chunk size, split it into parts
        while count_utf16_code_units(word) > chunk_size - 6:
            part, word = word[:chunk_size - 6], word[chunk_size - 6:]
            chunks.append(current_chunk + " " + part if current_chunk else part)
            current_chunk = word

        # Check if there is a previous chunk and will be a next chunk
        if i != 0 and i != len(words) - 1:
            # Adding 2 to account for the space that will be added, and 6 for the two dots
            condition = count_utf16_code_units(current_chunk + word + " ... ...") <= chunk_size
        else:
            # Adding 1 to account for the space that will be added, and 3 for the dots
            condition = count_utf16_code_units(current_chunk + word + " ...") <= chunk_size

        if condition:
            # Add the word to the current chunk
            if current_chunk != "":
                current_chunk += " "
            current_chunk += word
        else:
            # The current word would make the chunk too long, so it's time to start a new chunk
            chunks.append(current_chunk)
            current_chunk = word

    # Only add the last chunk if it's not an empty string
    if current_chunk != "":
        chunks.append(current_chunk)

    return chunks


def sleep_while_checking_stop_flag(delay):
    start_time = time.time()
    while time.time() - start_time < delay:
        if stop_flag:
            return
        time.sleep(0.1)  # check every 100ms


def Chat_chunks(data="example", chunk_size=144, delay=1., initial_delay=1., nofify=True, address="/chatbox/input", ip='127.0.0.1', port=9000, convert_ascii=False):
    global thread, stop_flag

    # stop thread
    if thread and thread.is_alive():
        stop_flag = True
        thread.join()

    stop_flag = False

    thread = threading.Thread(target=send_chunks_v2, args=(data, chunk_size, delay, initial_delay, nofify, address, ip, port, convert_ascii))
    thread.start()


def Chat_scrolling_chunks(data="example", chunk_size=144, delay=1., initial_delay=1., scroll_size=1, nofify=True, address="/chatbox/input", ip='127.0.0.1', port=9000, convert_ascii=False):
    global thread, stop_flag

    # stop thread
    if thread and thread.is_alive():
        stop_flag = True
        thread.join()

    stop_flag = False

    thread = threading.Thread(target=send_scrolling_chunks, args=(data, chunk_size, delay, initial_delay, scroll_size, nofify, address, ip, port, convert_ascii))
    thread.start()


# send chat by chunks
def send_chunks(text, chunk_size=144, delay=1., initial_delay=1., nofify=True, address="/chatbox/input", ip='127.0.0.1', port=9000, convert_ascii=False):
    # Convert text to list of UTF-16 code units
    text_utf16 = text.encode('utf-16le')

    # Check if text is shorter than chunk_size
    if count_utf16_code_units(text) <= chunk_size:
        Chat(text, send=True, nofify=nofify, address=address, IP=ip, PORT=port, convert_ascii=convert_ascii)
        return

    # Calculate the number of chunks
    num_chunks = count_utf16_code_units(text) // chunk_size + (count_utf16_code_units(text) % chunk_size != 0)

    for i in range(num_chunks):
        if stop_flag:
            break

        # Get the current chunk
        chunk = text[i*chunk_size:(i+1)*chunk_size]

        # Convert chunk back to string
        chunk = chunk.decode('utf-16le')

        # Send the chunk to the API
        Chat(chunk, send=True, nofify=(nofify and i == 0), address=address, IP=ip, PORT=port, convert_ascii=convert_ascii)

        # Wait for the specified delay
        if i == 0:
            sleep_while_checking_stop_flag(initial_delay)
        else:
            sleep_while_checking_stop_flag(delay)


def send_chunks_v2(text, chunk_size=144, delay=1., initial_delay=1., nofify=True, address="/chatbox/input", ip='127.0.0.1', port=9000, convert_ascii=False):
    # Send the full text if it fits into a single chunk
    if count_utf16_code_units(text) <= chunk_size:
        Chat(text, send=True, nofify=nofify, address=address, IP=ip, PORT=port, convert_ascii=convert_ascii)
        return

    chunks = split_words(text, chunk_size)
    for i, chunk in enumerate(chunks):
        if stop_flag:
            break

        # Add dots to indicate continuation
        if i != 0:
            chunk = "... " + chunk  # Add a space after the dots
        if i != len(chunks) - 1:
            chunk = chunk + " ..."  # Add a space before the dots

        # Send the chunk to the API
        Chat(chunk, send=True, nofify=(nofify and i == 0), address=address, IP=ip, PORT=port, convert_ascii=convert_ascii)

        # Wait for the specified delay
        if i == 0:
            sleep_while_checking_stop_flag(initial_delay)
        else:
            sleep_while_checking_stop_flag(delay)


# send chat by scrolling chunks
def send_scrolling_chunks(text, chunk_size=144, delay=1., initial_delay=1., scroll_size=1, nofify=True, address="/chatbox/input", ip='127.0.0.1', port=9000, convert_ascii=False):
    # Convert text to list of UTF-16 code units
    text_utf16 = text.encode('utf-16le')

    # Check if text is shorter than chunk_size
    if count_utf16_code_units(text) <= chunk_size:
        Chat(text, send=True, nofify=nofify, address=address, IP=ip, PORT=port, convert_ascii=convert_ascii)
        return

    # Calculate the number of chunks
    num_chunks = (count_utf16_code_units(text) - chunk_size) // scroll_size + 1

    for i in range(num_chunks):
        if stop_flag:
            break

        # Get the current chunk
        chunk_utf16 = text_utf16[i*scroll_size*2:(i*scroll_size*2)+chunk_size*2]

        # Convert chunk back to string
        chunk = chunk_utf16.decode('utf-16le')

        # Send the chunk to the API
        Chat(chunk, send=True, nofify=(nofify and i == 0), address=address, IP=ip, PORT=port, convert_ascii=convert_ascii)

        # Wait for the specified delay
        if i == 0:
            sleep_while_checking_stop_flag(initial_delay)
        else:
            sleep_while_checking_stop_flag(delay)


def actionChatbox(client, str):
    # bundle
    bundle_builder = OscBundleBuilder(osc_bundle_builder.IMMEDIATELY)
    # Create a new message.
    message_builder = OscMessageBuilder(address="/chatbox/input")
    message_builder.add_arg(str)
    message_builder.add_arg(True)
    message_builder.add_arg(True)
    msg = message_builder.build()

    # Add the message to the bundle.
    bundle_builder.add_content(msg)

    # Build and get the bundle.
    bundle = bundle_builder.build()
    client.send_message("/chatbox/typing", True)
    time.sleep(1)
    client.send_message("/chatbox/typing", False)
    client.send(bundle)

def acitonMove(client,direction, timee ,isRunning):
    if (direction=="forward"):
        client.send_message("/input/MoveForward", 1)
    if (direction=="backward"):
        client.send_message("/input/MoveBackward", 1)
    if (direction=="left"):
        client.send_message("/input/MoveLeft", 1)
    if (direction=="right"):
        client.send_message("/input/MoveRight", 1)
    if (isRunning==True):
        client.send_message("/input/Run", 1)
    time.sleep(timee)
    client.send_message("/input/MoveForward", False)
    client.send_message("/input/MoveBackward", False)
    client.send_message("/input/MoveLeft", False)
    client.send_message("/input/MoveRight", False)
    client.send_message("/input/Run", False)
    return 0

def acitonForceStopmoveing(client):
    client.send_message("/input/MoveForward", False)
    client.send_message("/input/MoveBackward", False)
    client.send_message("/input/MoveLeft", False)
    client.send_message("/input/MoveRight", False)
    client.send_message("/input/Run", False)
    return 0
"""
/input/LookLeft : Turn to the left while this is 1. Smooth in Desktop, VR will do a snap-turn if Comfort Turning is on.
"""
def acitonLook_left(client,value):
    client.send_message("/input/LookLeft", 1)
    time.sleep(0.05 * value)
    client.send_message("/input/LookLeft", False)
    return 0

"""
/input/LookRight : Turn to the right while this is 1. Smooth in Desktop, VR will do a snap-turn if Comfort Turning is on.
"""

def acitonLook_right(client,value):
    client.send_message("/input/LookRight", 1)
    time.sleep(0.05 * value)
    client.send_message("/input/LookRight", False)
    return 0

"""
/input/Jump : Jump if the world supports it.
"""

def acitonJump(client):
    client.send_message("/input/Jump", False)
    client.send_message("/input/Jump", 1)
    client.send_message("/input/Jump", False)
