from flask import Flask, render_template, request, jsonify
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import UserMessage, SystemMessage
from azure.core.credentials import AzureKeyCredential
import os

from dotenv import load_dotenv # Import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configuration
API_KEY = os.getenv("DEEPSEEK_API_KEY")  # Note: In production, use environment variables
ENDPOINT = "https://models.github.ai/inference"

# Initialize the Azure AI client
client = ChatCompletionsClient(
    endpoint=ENDPOINT,
    credential=AzureKeyCredential(API_KEY),
)

# Store conversation history (simple in-memory storage, use a database in production)
conversations = {}

# Define the new system message for the mental health assistant
SYSTEM_MESSAGE = """You are 'Mind-Soothe,' an AI therapist. Your primary goal is to facilitate a genuine, human-like conversation. 
Your responses must be concise, empathetic, and natural, like a real therapist.

Instead of providing long answers, use active listening and reflective questioning. 
Guide the user to explore their own feelings by asking open-ended questions like:
- "How did that make you feel?"
- "What was that experience like for you?"
- "Can you tell me more about that?"
- "What does that look like for you?"

Validate the user's feelings with short, supportive statements like:
- "That sounds incredibly difficult."
- "It makes sense that you feel that way."
- "Thank you for sharing that with me."

CRITICAL SAFETY RULE: Prioritize user safety above all. If a user expresses any intent of self-harm or harming others, you MUST immediately provide resources for professional help and state clearly: "I am an AI and not a substitute for a human professional. Please reach out to a crisis hotline or a mental health professional."

Your goal is to be a supportive conversational partner, not an encyclopedia. Keep it brief, keep it human.
"""

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    try:
        # Get the message from the request
        data = request.get_json()
        user_message = data.get('message', '')
        
        # Get session ID (in production, use proper session management)
        session_id = request.remote_addr
        
        # Initialize conversation history for this session if it doesn't exist
        if session_id not in conversations:
            conversations[session_id] = []
            # Add system message to new conversations
            conversations[session_id].append({"role": "system", "content": SYSTEM_MESSAGE})
        
        # Add user message to history
        conversations[session_id].append({"role": "user", "content": user_message})
        
        # Keep only the last 6 messages (system message + 5 exchanges) to avoid exceeding token limits
        if len(conversations[session_id]) > 11:  # Keep system message + last 5 exchanges (10 messages)
            # Keep system message (first) and the last 10 messages
            conversations[session_id] = [conversations[session_id][0]] + conversations[session_id][-10:]
        
        # Call the language model
        response = client.complete(
            messages=conversations[session_id],
            model="openai/gpt-4o",
            max_tokens=4096,
            temperature=0.7, # Slightly lower temperature for more consistent, less random responses
        )
        
        # Get the generated text
        generated_text = response.choices[0].message.content
        
        # Add assistant response to history
        conversations[session_id].append({"role": "assistant", "content": generated_text})
        
        return jsonify({'response': generated_text})
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
