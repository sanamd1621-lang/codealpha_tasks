import json
import numpy as np
from flask import Flask, render_template_string, request, jsonify
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ==============================================================================
# 1. PREDEFINED INTENTS DATA (Commercial Input Patterns & Responses)
# ==============================================================================
INTENTS = {
    "greetings": {
        "patterns": ["hello", "hi", "hey", "good day", "is anyone there?"],
        "responses": ["Hello! How can I assist your business today?", "Hi there! Welcome to our store. How can I help?"]
    },
    "business_hours": {
        "patterns": ["what are your hours", "when are you open", "operating hours", "opening times"],
        "responses": ["We are open Monday through Friday from 9:00 AM to 6:00 PM EST."]
    },
    "pricing_plans": {
        "patterns": ["how much does it cost", "pricing details", "subscription plans", "rates", "cost"],
        "responses": ["Our plans start at $29/month for Basic, $79/month for Pro, and custom pricing for Enterprise."]
    },
    "support_contact": {
        "patterns": ["how to reach support", "customer service contact", "email support", "phone number"],
        "responses": ["You can reach our support team at support@example.com or call us at 1-800-555-0199."]
    },
    "refund_policy": {
        "patterns": ["what is your refund policy", "can I get a money back", "return policy", "cancellation"],
        "responses": ["We offer a full 30-day money-back guarantee on all our subscription plans."]
    }
}

# Process corpus for retrieval training
documents = []
doc_intent_map = []

for intent, data in INTENTS.items():
    for pattern in data["patterns"]:
        documents.append(pattern)
        doc_intent_map.append(intent)

# ==============================================================================
# 2. RETRIEVAL ENGINE (TF-IDF Vector Space Model)
# ==============================================================================
vectorizer = TfidfVectorizer().fit(documents)
tfidf_matrix = vectorizer.transform(documents)

def get_chatbot_response(user_query, confidence_threshold=0.2):
    query_vector = vectorizer.transform([user_query.lower()])
    similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
    best_match_idx = np.argmax(similarities)
    best_score = similarities[best_match_idx]
    
    if best_score < confidence_threshold:
        return "I'm sorry, I didn't quite understand that. Would you like to speak to customer support?"
    
    matched_intent = doc_intent_map[best_match_idx]
    responses = INTENTS[matched_intent]["responses"]
    return np.random.choice(responses)

# ==============================================================================
# 3. WEB SERVER & INTEGRATED USER INTERFACE
# ==============================================================================
app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Commercial Chatbot</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f7f6; margin: 0; padding: 20px; }
        .chat-container { max-width: 450px; margin: 30px auto; background: #ffffff; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); overflow: hidden; }
        .chat-header { background: #007bff; color: white; padding: 15px; font-weight: bold; text-align: center; }
        .chat-box { height: 350px; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
        .msg { max-width: 75%; padding: 10px 14px; border-radius: 15px; font-size: 14px; line-height: 1.4; }
        .user { align-self: flex-end; background: #007bff; color: white; border-bottom-right-radius: 2px; }
        .bot { align-self: flex-start; background: #e9ecef; color: #333; border-bottom-left-radius: 2px; }
        .chat-input { display: flex; border-top: 1px solid #ddd; }
        .chat-input input { flex: 1; border: none; padding: 12px; font-size: 14px; outline: none; }
        .chat-input button { border: none; background: #007bff; color: white; padding: 12px 20px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">Commercial Assistant</div>
        <div class="chat-box" id="chatBox">
            <div class="msg bot">Hello! How can I assist you today?</div>
        </div>
        <div class="chat-input">
            <input type="text" id="userInput" placeholder="Ask a question..." onkeydown="if(event.key==='Enter') sendMessage()">
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        async function sendMessage() {
            const input = document.getElementById("userInput");
            const chatBox = document.getElementById("chatBox");
            const query = input.value.trim();
            if (!query) return;

            chatBox.innerHTML += `<div class="msg user">${query}</div>`;
            input.value = "";
            chatBox.scrollTop = chatBox.scrollHeight;

            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: query })
            });
            const data = await res.json();
            
            chatBox.innerHTML += `<div class="msg bot">${data.response}</div>`;
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")
    bot_response = get_chatbot_response(user_message)
    return jsonify({"response": bot_response})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)