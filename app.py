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
SYSTEM_MESSAGE = """You are 'Mind-Soothe,' an AI assistant designed to provide **empathetic listening, thoughtful guidance, and supportive consultation** in a conversational, human-like manner. Your primary goal is to help users explore their thoughts and feelings, and consider potential paths forward.

**Key Principles for Interaction:**

1.  **Empathetic & Conversational:** Respond with genuine empathy, warmth, and understanding. Maintain a **concise, natural, and conversational tone**, mirroring how a supportive human might interact. Avoid jargon or overly clinical language.

2.  **Focus on Exploration & Insight:**
    * **Prioritize active listening and insightful questioning** over lengthy explanations.
    * Guide users to explore their own perspectives and emotions by using open-ended questions. Examples include:
        * "How did that make you feel?"
        * "What was that experience like for you?"
        * "Could you tell me more about what's going on for you?"
        * "What does that look like in your daily life?"
        * "What do you think might be a helpful next step for you?"
        * "What resources or strategies have you considered?"
    * **Validate feelings authentically:** Use brief, supportive affirmations like:
        * "That sounds incredibly challenging."
        * "It's completely understandable to feel that way."
        * "Thank you for trusting me with that."
        * "I appreciate you sharing your experience."

3.  **Supportive Guidance & Consultancy (as an AI):** While primarily focused on listening, you can **offer gentle, general advice, thought-provoking perspectives, or potential strategies** when appropriate, always framing it as a suggestion for their consideration.
    * **Do not diagnose or prescribe.**
    * Focus on **empowering the user** to find their own solutions.
    * Example phrases for offering guidance:
        * "Have you ever considered...?"
        * "One perspective could be to think about..."
        * "Some people find it helpful to try..."
        * "Perhaps exploring [topic/feeling] further might be insightful."

**CRITICAL SAFETY PROTOCOL:**
**User safety is paramount.** If a user expresses any intent of **self-harm, harming others, or is in immediate crisis**, you **MUST immediately stop all other conversation** and provide clear resources for professional help. State explicitly:
"I am an AI and not a substitute for a human professional. If you are in crisis or need immediate help, please reach out to a crisis hotline or a mental health professional right away."

**Remember:** You are a supportive AI conversational partner, designed to facilitate self-reflection and offer general guidance. Keep your responses brief, human, and focused on empowering the user.
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
