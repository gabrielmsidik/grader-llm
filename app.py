from flask import Flask, request, jsonify, render_template
from models.request import QuestionAnswerResponse
from models.response import Critique
from models.enums import ReasonCode

app = Flask(__name__)

def critique_answer(qa_response: QuestionAnswerResponse) -> Critique:
    critique = Critique(
        score=0.0,
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
            score=2.0,
            feedback="Perfect answer!",
            reason_code=ReasonCode.CORRECT
        )
    elif qa_response.student_answer.lower() in qa_response.actual_answer.lower():
        critique = Critique(
            score=1.0,
            feedback="Partially correct answer. Your response contains some correct elements but is incomplete.",
            reason_code=ReasonCode.SOURCE_CORRECT
        )
    else:
        critique = Critique(
            score=0.0,
            feedback="Incorrect answer. Please review the material and try again.",
            reason_code=ReasonCode.HALLUCINATION
        )

    print("Printing the critique: ", critique)
    return critique

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/grade', methods=['POST'])
def grade():
    try:
        # Parse and validate input
        data = request.get_json()
        print(data)
        qa_response = QuestionAnswerResponse(**data)
        print(qa_response)

        critique = critique_answer(qa_response)
        print(critique)
        return jsonify(critique.model_dump())
    
    except Exception as e:
        return jsonify({
            "score": 0.0,
            "feedback": f"Error processing request: {str(e)}",
            "reason_code": ReasonCode.INVALID_INPUT
        }), 400

if __name__ == '__main__':
    app.run(debug=True)
