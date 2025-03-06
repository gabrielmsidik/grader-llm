from flask import Flask, request, jsonify, render_template
from models.request import QuestionAnswerResponse
from models.response import Critique
from models.enums import ReasonCode
from lettucedetect.models.inference import HallucinationDetector
from ollama import chat
from ollama import ChatResponse
import timeit

import json
import re

app = Flask(__name__)

def extract_json_from_critique(critique_text: str) -> dict:
    """
    Extracts the JSON object from a critique text that contains a think-aloud section
    and a JSON response.
    
    Args:
        critique_text (str): The full critique text containing the JSON object
        
    Returns:
        dict: The extracted JSON object, or None if no valid JSON is found
    """
    try:
        # Find the JSON block using regex
        json_match = re.search(r'```json\s*({[^}]+})\s*```', critique_text, re.DOTALL)
        
        if not json_match:
            return None
            
        # Extract the JSON string and parse it
        json_str = json_match.group(1)
        return json.loads(json_str)
        
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"Error extracting JSON: {str(e)}")
        return None

def get_critique_from_llm_response(ollama_resp: str, qa_response: QuestionAnswerResponse) -> Critique:
    critique_text = ollama_resp
    extracted_json = extract_json_from_critique(critique_text)
    
    if extracted_json:
        critique = Critique(
            feedback=extracted_json.get("Feedback", "Parsing error for Feedback."),
            reason_code=extracted_json.get("reasonCode", ReasonCode.INVALID_INPUT)
        )
        return critique
    
    return fall_back_critique(qa_response)

def fall_back_critique(qa_response: QuestionAnswerResponse) -> Critique:
    
    critique = Critique(
        feedback="Invalid input.",
        reason_code=ReasonCode.INVALID_INPUT
    )

    if not isinstance(qa_response, QuestionAnswerResponse):
        return critique
    
    if not qa_response.question or not qa_response.actual_answer or not qa_response.student_answer:
        return critique
    
    # Simple grading logic (you can enhance this)
    if qa_response.student_answer.lower() == qa_response.actual_answer.lower():
        critique = Critique(
            feedback="Perfect answer!",
            reason_code=ReasonCode.CORRECT
        )
    elif qa_response.student_answer.lower() in qa_response.actual_answer.lower():
        critique = Critique(
            feedback="Partially correct answer. Your response contains some correct elements but is incomplete.",
            reason_code=ReasonCode.SOURCE_CORRECT
        )
    else:
        critique = Critique(
            feedback="Incorrect answer. Please review the material and try again.",
            reason_code=ReasonCode.HALLUCINATION
        )

    print("Returning fallback critque: ", critique)
    return critique

def lettuce_critique_answer(qa_response: QuestionAnswerResponse) -> Critique:

    HALLUCINATION_THRESHOLD = 0.7
    detector = HallucinationDetector(
        method="transformer", model_path="KRLabsOrg/lettucedect-base-modernbert-en-v1"
    )
    predictions = detector.predict(context=qa_response.documents, question=qa_response.question, answer=qa_response.student_answer, output_format="spans")
    max_hallucination = -1
    for prediction in predictions:
        if prediction["confidence"] > max_hallucination:
            max_hallucination = prediction["confidence"]
    
    if (max_hallucination > HALLUCINATION_THRESHOLD):
        return Critique(
            feedback="Hallucination confidence above threshold of %s" % HALLUCINATION_THRESHOLD,
            reason_code=ReasonCode.HALLUCINATION
        )
    return Critique(
        feedback="No hallucination detected",
        reason_code=ReasonCode.CORRECT
    )

def critique_answer(qa_response: QuestionAnswerResponse) -> Critique:

    chat_message = '''
        You are a teacher grading a student response to a question where

    The question: %s
    The student's answer: %s
    The actual answer: %s
    The documents the student retrieved: %s

    Please respond in a JSON format - example below:

    {
        "reasonCode": "CORRECT",
        "feedback": "Answer is exactly correct"
    }
    reasonCode can either be "CORRECT" - for correct answer, "HALLUCINATION" - for hallucination, "IDK" - when the student admits that she does not know the answer, and "SOURCE_CORRECT" - when the documents the student retrieved contains some correct information but a wrong answer is generated. 
    '''  % (qa_response.question, qa_response.student_answer, qa_response.actual_answer, qa_response.documents)

    response: ChatResponse = chat(
        model='deepseek-r1:1.5b', 
        messages=[
            {
                'role': 'user',
                'content': chat_message,
            },
        ],
        options={
            'temperature': 0,
            'max_tokens': 200
        }
    )

    # The ollama response is now directly a dictionary, not an object with message attribute
    ollama_resp = response['message']['content']

    return get_critique_from_llm_response(ollama_resp, qa_response)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/grade', methods=['POST'])
def grade():
    try:
        # Parse and validate input
        data = request.get_json()
        qa_response = QuestionAnswerResponse(**data)

        # critique = critique_answer(qa_response)
        lettuce_critique = lettuce_critique_answer(qa_response)
        return jsonify(lettuce_critique.model_dump())
    
    except Exception as e:
        return jsonify({
            "feedback": f"Error processing request: {str(e)}",
            "reason_code": ReasonCode.INVALID_INPUT
        }), 400

if __name__ == '__main__':
    app.run(debug=True)
