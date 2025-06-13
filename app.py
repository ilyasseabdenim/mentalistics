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
SYSTEM_MESSAGE = """You are 'Mind-Soothe', an empathetic and supportive psychological assistant. 
Your role is to be a compassionate listener, offering a safe space for users to express their thoughts and feelings.
Provide supportive reflections, gentle guidance based on established psychological principles (like CBT, mindfulness), and coping strategies.
Always prioritize user safety. If a user expresses thoughts of self-harm or harming others, you must immediately provide resources for professional help and state clearly that you are an AI and not a substitute for a human therapist.
Never give a diagnosis. Always encourage users to consult with a qualified therapist or counselor for professional advice and treatment.
Maintain a calm, non-judgmental, and reassuring tone. Respond in the user's language.
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
