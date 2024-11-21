from deepgram import Deepgram
import asyncio

import json
import sys
from dotenv import load_dotenv
import os
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
load_dotenv()

DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY")


FILE = './speech/current_conversation.wav'

# if os.path.isfile(file_path):
#     print(f'The file {file_path} is a regular file.')
# else:
#     print(f'The file {file_path} is not a regular file or does not exist.')

MIMETYPE = 'audio/wav'


async def main():

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

    # Write only the transcript to the console
    # print(response["results"]["channels"][0]["alternatives"][0]["transcript"])
def transTTDeepgram():
    try:
        # If running in a Jupyter notebook, Jupyter is already running an event loop, so run main with this line instead:
        # await main()
        res = asyncio.run(main())
    except Exception as e:
        exception_type, exception_object, exception_traceback = sys.exc_info()
        line_number = exception_traceback.tb_lineno
        print(f'line {line_number}: {exception_type} - {e}')

    # print(f"res: {res}")
    transcript = res.get("results", {}).get("channels", [{}])[0].get(
        "alternatives", [{}])[0].get("transcript", "")
    print(transcript)
    return transcript


# transcript = res["results"]["channels"][0]["alternatives"][0]["transcript"]
