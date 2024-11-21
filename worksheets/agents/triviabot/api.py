import os
import re
from uuid import UUID, uuid4

from worksheets.llm import llm_generate


def ask_question(question_number: int):
    question_number = int(question_number)
    questions = [
        ["A ____ atom in an atomic clock beats 9,192,631,770 times a second", "cesium"],
        ["A ____ is the blue field behind the stars", "canton"],
        ["A ____ takes 33 hours to crawl one mile", "snail"],
        ["A ____ written to celebrate a wedding is called a epithalamium", "poem"],
        ["A 'sirocco' refers to a type of ____", "wind"],
        ["A 3 1/2' floppy disk measures ____ & 1/2 inches across", "three"],
        [
            "A 300,000 pound wedding dress made of platinum was once exhibited, and in the instructions from the designer was a warning. What was it",
            "do not iron",
        ],
        ["A bird in the hand is worth ____", "two in the bush"],
        ["A block of compressed coal dust used as fuel", "briquette"],
        ["A blockage in a pipe caused by a trapped bubble of air", "airlock"],
        ["A blunt thick needle for sewing with thick thread or tape", "bodkin"],
    ]

    if question_number > len(questions):
        return {"question": "No more questions available"}

    return {"question": questions[question_number - 1][0]}


def check_user_answer(question_number: int, answer: str):
    question_number = int(question_number)
    questions = [
        ["A ____ atom in an atomic clock beats 9,192,631,770 times a second", "cesium"],
        ["A ____ is the blue field behind the stars", "canton"],
        ["A ____ takes 33 hours to crawl one mile", "snail"],
        ["A ____ written to celebrate a wedding is called a epithalamium", "poem"],
        ["A 'sirocco' refers to a type of ____", "wind"],
        ["A 3 1/2' floppy disk measures ____ & 1/2 inches across", "three"],
        [
            "A 300,000 pound wedding dress made of platinum was once exhibited, and in the instructions from the designer was a warning. What was it?",
            "do not iron",
        ],
        ["A bird in the hand is worth ____", "two in the bush"],
        ["What is a block of compressed coal dust used as fuel called?", "briquette"],
        [
            "What is a blockage in a pipe caused by a trapped bubble of air called?",
            "airlock",
        ],
        [
            "What is a blunt thick needle for sewing with thick thread or tape?",
            "bodkin",
        ],
    ]

    current_dir = os.path.dirname(os.path.realpath(__file__))
    prompt_dir = os.path.join(current_dir, "prompts")

    response = llm_generate(
        "check_answer.prompt",
        {
            "question": questions[question_number - 1][0],
            "answer": questions[question_number - 1][1],
            "user_response": answer,
        },
        prompt_dir,
        model_name="azure/gpt-4o",
        max_tokens=100,
        temperature=0.0,
    )

    answer = re.findall(r"<answer>(.*?)</answer>", response, re.DOTALL)
    if answer:
        answer = True if answer[0].strip().lower() == "true" else False

        return {"correct": answer}

    return {"correct": False, "correct_answer": questions[question_number - 1][1]}
