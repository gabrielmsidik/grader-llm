# grader-llm
LLM judge that compares and grades questions and answers

# Steps for running the application locally
1. Create virtual environment for the first time (Only do this once) - python -m venv .my_venv
2a. (For Windows) run - .\.my_venv\Scripts\activate
2b. (For Mac) run - source .my_venv/bin/activate
3. pip install -r requirements.txt
4. python app.py
5. After changes - do a pip freeze - to check if any new packages were added in developing a new feature
6. Add new packages to requirements.txt

Note that for ollama integration - ollama needs to be running locally 