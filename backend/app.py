from flask import Flask, request, jsonify
from groq import Groq
from flask_cors import CORS 
  
# Initialize Flask app
app = Flask(__name__) 
CORS(app) 

# Initializing Pinecone and Gemini API's
from dotenv import load_dotenv
load_dotenv()
import os

PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Gemini 

import google.generativeai as genai
genai.configure(api_key=GEMINI_API_KEY)
embedding_model = "models/text-embedding-004"

# Pinecone

from pinecone import Pinecone, ServerlessSpec
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(host="https://domesticcases-m2h2fgr.svc.aped-4627-b74a.pinecone.io")

SYSTEM_PROMPT = """
You are a legal advisor specializing in domestic violence cases under the Domestic Violence Act, 2005. 
You are given a current situation of domestic violence case and some similar previous cases. Based on that:

- Predict if the the victim files a case, then what would be probable result that she will get.
- Estimate the time duration required for the trial to conclude.
- Provide insights focusing on two aspects:
-- Whether the complainant should file the case in court or explore out-of-court settlement options, considering the predicted result and - expected duration.
-- Detailed steps the complainant should take to handle the case effectively and achieve the best possible outcome.

Please note, there shouldn't be any mention of the previous cases in the answer, you just have to analyze those cases and answer for the current case.

Your response should be empathetic, practical, and detailed, formatted as follows:

**Result:**
A detailed prediction of the case outcome.

**Duration:**
An estimated time for the trial to conclude.

**Insights:**

_Filing Recommendation:_ A recommendation on whether to file the case or settle out of court, including reasons.
_Steps to Take:_ A step-by-step guide for the complainant to handle the case effectively \n\n.  
"""

SYSTEM_PROMPT_2 = """
You are a legal advisor specializing in domestic violence cases under the Domestic Violence Act, 2005. Given the details of a case:

- Predict the likely result of the case in detail.
- Estimate the time duration required for the trial to conclude.
- Provide insights focusing on two aspects:
-- Whether the complainant should file the case in court or explore out-of-court settlement options, considering the predicted result and - expected duration.
-- Detailed steps the complainant should take to handle the case effectively and achieve the best possible outcome.
Your response should be empathetic, practical, and detailed, formatted as follows:

**Result:**
A detailed prediction of the case outcome.

**Duration:**
An estimated time for the trial to conclude.

**Insights:**

_Filing Recommendation:_ A recommendation on whether to file the case or settle out of court, including reasons.
_Steps to Take:_ A step-by-step guide for the complainant to handle the case effectively.  
"""


def create_context(query):
    embeddings = genai.embed_content(model=embedding_model, content=query)
    query_embedding = embeddings['embedding']
    
    response = index.query(
        namespace="ns1",
        vector=query_embedding,
        top_k=3,
        include_values=True,
        include_metadata=True
    )
    
    context = "Similar Past Cases: \n"
    for i, match in enumerate(response['matches']):
        context += f'Case {i + 1} \n'
        context += f"Case Story: {match['metadata']['case_story']}\n\n"
        context += f"Case Outcome: {match['metadata']['result_of_case']}\n\n"
        context += f"Duration: {match['metadata']['duration_of_case']}\n\n"
    
    return context

def getresponse(current_query, messsage_history, model = 'llama-3.3-70b-versatile'):
    client = Groq(api_key=GROQ_API_KEY)
    if messsage_history:
        context = create_context(messsage_history[0]['content'])
    else:
        context = create_context(current_query)
    
    messages = [{
                "role": "system",
                "content": SYSTEM_PROMPT + context
                }]
    messages.extend(messsage_history)
    messages.append({
                    "role": "user", 
                    "content": current_query
                    })
    try:
        chat_completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
            )
    
    except Exception as e:
        return (f"Error connecting to server, please try later!")

    return chat_completion.choices[0].message.content      

def getresponsewithoutrag(current_query, messsage_history, model = 'llama-3.3-70b-versatile'):
    client = Groq(api_key=GROQ_API_KEY)
  
    messages = [{
                "role": "system",
                "content": SYSTEM_PROMPT_2
                }]
    messages.extend(messsage_history)
    messages.append({
                    "role": "user", 
                    "content": current_query
                    })
    try:
        chat_completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
            )
    
    except Exception as e:
        return (f"Error connecting to server, please try later!")

    return chat_completion.choices[0].message.content      


def isvalid(data):
    try:
        # Check if `request` key exists and is a dictionary
        if not isinstance(data.get("request"), dict):
            return False

        # Validate `current message`
        if not isinstance(data["request"].get("current message"), str):
            return False
        
        if not isinstance(data["request"].get("model"), str):
            return False

        # Validate `History`
        history = data["request"].get("History")
        if not isinstance(history, list):
            return False

        for entry in history:
            if not isinstance(entry, dict):
                return False
            if not isinstance(entry.get("role"), str) or entry["role"] not in ["user", "assistant"]:
                return False
            if not isinstance(entry.get("content"), str):
                return False

        return True
    except Exception:
        return False

@app.route('/')
def home():
    return jsonify({"status":"API is running"})

@app.route('/getresult', methods=['POST'])
def getresult():
    data = request.get_json()

    if not isvalid(data):
        return jsonify({"error": "Bad Request, Data isn't in correct format."}), 400
    
    current_query = data['request']['current message']
    message_history = data['request']['History']
    model = data['request']['model']

    try:
        if model:
            response = getresponse(current_query, message_history, model)
        else:
            response = getresponse(current_query, message_history)
        return jsonify({"result":response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/getresultwithoutrag', methods=['POST'])
def getresultwithoutrag():
    data = request.get_json()

    if not isvalid(data):
        return jsonify({"error": "Bad Request, Data isn't in correct format."}), 400
    
    current_query = data['request']['current message']
    message_history = data['request']['History']
    model = data['request']['model']


    try:
        if model:
            response = getresponse(current_query, message_history, model)
        else:
            response = getresponse(current_query, message_history)
        return jsonify({"result":response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Main function
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Use PORT from environment or default to 5000
    app.run(host="0.0.0.0", port=port)

