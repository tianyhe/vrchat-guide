# import csv
# from enum import Enum
# from datetime import datetime
#
#
# class LogElements(Enum):
#     MESSAGE = "Message"
#     IMPORTANT_OBSERVATIONS = "Important Observations"
#     IMPORTANT_SCORES = "Important Scores"
#     NPC_RESPONSE = "NPC Response"
#     TIME_FOR_INPUT = "Time for Input"
#     TIME_FOR_HUMAN_SPEECH_RECOGNITION = "Time for Human speech detection"
#     TIME_FOR_VOICE_NORMALIZATION = "Time for voice normalization"
#     TIME_FOR_AUDIO_RECORD = "Time for audio recording"
#     TIME_AUDIO_TO_TEXT = "Time for Audio to Text"
#     TIME_RETRIEVAL = "Time for Retrieval"
#     TIME_FOR_RESPONSE = "Time for Response"
#     TIME_FOR_CONTROLEXP = "Time for Expression"
#     TIME_FOR_TTS = "Time for TextToSpeech"
#     SUMMARY= "Summary"
#     SUMMARY1 = "Summary1"
#
#
# class CSVLogger:
#     enum_values = {}
#     initialize_header = True
#     curr_time = datetime.now(tz=None)
#     curr_time = curr_time.strftime("%Y-%m-%d_%H-%M")
#     curr_file = f"evaluations\CSV_LOGS_{curr_time}.csv"
#
#     def set_enum(self, enum: Enum, result):
#         self.enum_values[enum.value] = result
#
#     def write_to_csv(self, log_values=True):
#         headers = [header.value for header in LogElements]
#         if log_values:
#             with open(self.curr_file, "a", newline="", encoding="utf-8") as csv_file:
#                 csv_writer = csv.DictWriter(csv_file, fieldnames=headers)
#                 if self.initialize_header:
#                     csv_writer.writeheader()
#                     self.initialize_header = False
#                 csv_writer.writerow(self.enum_values)
#

import csv
import os
# from enum import Enum
# from datetime import datetime
#
#
# class LogElements(Enum):
#     MESSAGE = "Message"
#     IMPORTANT_OBSERVATIONS = "Important Observations"
#     IMPORTANT_SCORES = "Important Scores"
#     NPC_RESPONSE = "NPC Response"
#     TIME_FOR_INPUT = "Total time for Input"
#     TIME_FOR_HUMAN_SPEECH_RECOGNITION = "Time for Human speech detection"
#     TIME_FOR_VOICE_NORMALIZATION = "Time for voice normalization"
#     TIME_FOR_AUDIO_RECORD = "Time for audio recording"
#     TIME_AUDIO_TO_TEXT = "Time for Audio to Text"
#     TIME_RETRIEVAL = "Time for Retrieval"
#     TIME_FOR_RESPONSE = "Time for Response"
#
#
# class CSVLogger:
#     enum_values = {}
#     initialize_header = True
#     curr_time = datetime.now(tz=None)
#     curr_time = curr_time.strftime("%Y-%m-%d_%H-%M")
#     # curr_file = f"../evaluations/TestScenarios_CSV/CSV_LOGS_{curr_time}.csv"
#     curr_file = f"evaluations\TestScenarios_CSV\CSV_LOGS_{curr_time}.csv"
#
#     def set_enum(self, enum: Enum, result):
#         self.enum_values[enum.value] = result
#
#     def write_to_csv(self, log_values=True):
#         headers = [header.value for header in LogElements]
#         if log_values:
#             with open(self.curr_file, "a", newline="", encoding="utf-8") as csv_file:
#                 csv_writer = csv.DictWriter(csv_file, fieldnames=headers)
#                 if self.initialize_header:
#                     csv_writer.writeheader()
#                     self.initialize_header = False
#                 csv_writer.writerow(self.enum_values)

import csv
import os
from enum import Enum
from datetime import datetime


class LogElements(Enum):
    MESSAGE = "Message"
    IMPORTANT_OBSERVATIONS = "Important Observations"
    IMPORTANT_SCORES = "Important Scores"
    NPC_RESPONSE = "NPC Response"
    TIME_FOR_INPUT = "Total time for Input"
    TIME_FOR_HUMAN_SPEECH_RECOGNITION = "Time for Human speech detection"
    TIME_FOR_VOICE_NORMALIZATION = "Time for voice normalization"
    TIME_FOR_AUDIO_RECORD = "Time for audio recording"
    TIME_AUDIO_TO_TEXT = "Time for Audio to Text"
    TIME_RETRIEVAL = "Time for Retrieval"
    TIME_FOR_RESPONSE = "Time for Response"
    TIME_FOR_REFLECTION = "Time for Reflection"
    TIME_FOR_GENERATE_OBS = "Time for Generate Observations"

class CSVLogger:
    enum_values = {}
    initialize_header = True
    curr_time = datetime.now(tz=None)
    curr_time = curr_time.strftime("%Y-%m-%d_%H-%M")
    curr_file = f"evaluations\TestScenarios_CSV\CSV_LOGS_{curr_time}.csv"

    def set_enum(self, enum: Enum, result):
        self.enum_values[enum.value] = result

    def write_to_csv(self, log_values=True):
        headers = [header.value for header in LogElements]
        if log_values:
            with open(self.curr_file, "a", newline="", encoding="utf-8") as csv_file:
                csv_writer = csv.DictWriter(csv_file, fieldnames=headers)
                if self.initialize_header:
                    csv_writer.writeheader()
                    self.initialize_header = False
                csv_writer.writerow(self.enum_values)