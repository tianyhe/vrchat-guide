import os
import math
import csv
import datetime
import numpy as np
import openai
from openai import OpenAI
from sentence_transformers import util
from collections import deque
from sklearn.preprocessing import MinMaxScaler
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("API_KEY")
openai_client = OpenAI(api_key=API_KEY)

engine = "text-embedding-ada-002"
DECAY_FACTOR = 0.995
RECENCY_WEIGHT = 1.0
RELEVANCE_WEIGHT = 1.0

currStatement = ""
resultObservation = []


def retrievalFunction(
        currentConversation: str,
        memoryStream: list,
        retrievalCount: int,
        isBaseDescription=True,
        is_reflection=True,
        is_publish_event=False,
):
    """
    Returns:
    - list: A list of tuples containing retrieval scores and retrieved observations.

    - Example return: [(1.0, 'John values family and views them as important.'), (0.9888348851281439, 'John Lin loves his family very much.'), (0.7962403715756174, 'John Lin values his family a lot.'), (0.4840372876913257, 'John Lin asks Katie if she has any kids.'), (0.40970729218079427, 'Katie and John are discussing their living situations.')]
    """
    if memoryStream:
        memoryStream = calculateRecency(memoryStream, isBaseDescription)
        memoryData = prepareMemoryData(memoryStream)

        observationData = []
        recencyScores = []

        for memory in memoryData:
            observationData.append(memory[0])
            recencyScores.append(memory[1])

        # only sort by recency if we are reflecting
        if is_reflection:
            reflection_results = sorted(
                zip(recencyScores, observationData),
                key=lambda x: x[0],
                reverse=True
            )[:retrievalCount]
            return reflection_results

        similarityScores = calculateRelevance(currentConversation, observationData)

        # only sort by relevance if we are publishing an event
        if is_publish_event:
            publish_results = sorted(
                zip(similarityScores, observationData),
                key=lambda x: x[0],
                reverse=True
            )[:retrievalCount]
            return publish_results

        return calculateRetrievalScore(
            observationData, recencyScores, similarityScores, retrievalCount
        )
    return []


def calculateRecency(memoryStream, isBaseDescription):
    for memory in memoryStream:
        if isBaseDescription:
            memory["Recency"] = 0
        else:
            currTime = datetime.datetime.utcnow()
            diffInSeconds = (currTime - memory["Creation Time"]).total_seconds()
            minutesDiff = diffInSeconds / 3600
            memory["Recency"] = math.exp(-DECAY_FACTOR * minutesDiff)
    return memoryStream


def calculateRelevance(currentConversation: str, observationData: list):
    contentEmbedding = (
        openai_client.embeddings.create(input=currentConversation, model=engine)
            .data[0]
            .embedding
    )
    dataEmbedding = openai_client.embeddings.create(input=observationData, model=engine)
    dataEmbedding = dataEmbedding.data
    dataEmbedding = [data.embedding for data in dataEmbedding]
    similarityVector = util.pytorch_cos_sim(contentEmbedding, dataEmbedding).tolist()[0]
    return similarityVector


def scaleScores(relevantObservations: list) -> list:
    retrievalScores = np.array(
        [observation[0] for observation in relevantObservations]
    ).reshape(-1, 1)

    minMaxScaler = MinMaxScaler()
    retrievalScores = minMaxScaler.fit_transform(retrievalScores)

    relevantObservations = list(
        zip(
            retrievalScores.flatten(),
            [observation[1] for observation in relevantObservations],
        )
    )
    return relevantObservations


def calculateRetrievalScore(
        observationData: list,
        recencyScores: list,
        similarityVector: list,
        retrievalCount: int,
):
    '''
    Returns:
    - list: A list of tuples containing retrieval scores and retrieved observations.

    Example:
    - Returned list: [(1.0, 'Observation1'), (0.363, 'Observation2'), (0.0, 'Observation3')]
    '''
    relevantObservations = []
    for idx, simScore in enumerate(similarityVector):
        retrievalScore = (
                recencyScores[idx] * RECENCY_WEIGHT + simScore * RELEVANCE_WEIGHT
        )
        currObservation = (retrievalScore, observationData[idx])
        relevantObservations.append(currObservation)
    relevantObservations = scaleScores(relevantObservations)
    relevantObservations = sorted(
        relevantObservations, key=lambda x: x[0], reverse=True
    )[:retrievalCount]

    return relevantObservations


def prepareMemoryData(memoryStream):
    memoryData = []
    for memory in memoryStream:
        recency = memory["Recency"]
        for observation in memory["Observations"]:
            memoryData.append((observation, recency))
    return memoryData


testQueue = deque(
    [
        {
            "Username": "John Lin",
            "Conversation with User": "Katie",
            "Creation Time": datetime.datetime(2023, 9, 30, 17, 58, 0, 928673),
            "Observations": [
                "Katie and John are discussing their living situations.",
                "John values family and views them as important.",
                "John shows interest in Katie's living situation.",
            ],
        },
        {
            "Username": "John Lin",
            "Conversation with User": "Katie",
            "Creation Time": datetime.datetime(2023, 9, 30, 17, 57, 43, 829009),
            "Observations": [
                "John Lin has a son named Eddy who is studying music theory.",
                "John Lin loves his family very much.",
                "John Lin asks Katie if she has any kids.",
            ],
        },
        {
            "Username": "John Lin",
            "Conversation with User": "Katie",
            "Creation Time": datetime.datetime(2023, 9, 30, 17, 57, 32, 155953),
            "Observations": [
                "John Lin values his family a lot.",
                "John Lin has a wife named Mei Lin.",
            ],
        },
    ]
)

# print(retrievalFunction("Hi John! tell me about your familly", testQueue, 5, True))

# [(1.0, 'John values family and views them as important.'), (0.9888348851281439, 'John Lin loves his family very much.'), (0.7962403715756174, 'John Lin values his family a lot.'), (0.4840372876913257, 'John Lin asks Katie if she has any kids.'), (0.40970729218079427, 'Katie and John are discussing their living situations.')]