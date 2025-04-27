import os
import google.generativeai as genai
import pyttsx3
from flask import Flask, render_template, request, jsonify, session
from typing import Dict, List
import uuid
import logging
import json

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure session key

# Initialize text-to-speech engine
try:
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 1.0)
    voices = engine.getProperty('voices')
    if voices:
        engine.setProperty('voice', voices[0].id)
    tts_enabled = True
except Exception as e:
    print(f"Text-to-speech initialization failed: {e}")
    tts_enabled = False
    engine = None

# Configure Gemini API
genai.configure(api_key="Enter_your_API_key")

# Mock API for job listings, events, and mentorship
class MockAPI:
    def __init__(self):
        self.job_data = [
            {"id": 1, "title": "Software Engineer", "company": "TechCorp", "location": "Remote", "type": "Full-Time"},
            {"id": 2, "title": "Marketing Manager", "company": "GrowEasy", "location": "Bangalore", "type": "Part-Time"}
        ]
        self.event_data = [
            {"id": 1, "name": "Women in Tech Summit", "date": "2025-05-15", "location": "Online"},
            {"id": 2, "name": "Career Restart Workshop", "date": "2025-06-10", "location": "Mumbai"}
        ]
        self.mentorship_data = [
            {"id": 1, "mentor": "Priya Sharma", "expertise": "Leadership", "availability": "Weekly"},
            {"id": 2, "mentor": "Anita Rao", "expertise": "Tech", "availability": "Bi-weekly"}
        ]

    def fetch_jobs(self, query: str) -> List[Dict]:
        return [job for job in self.job_data if query.lower() in job["title"].lower() or query.lower() in job["company"].lower()]

    def fetch_events(self, query: str) -> List[Dict]:
        return [event for event in self.event_data if query.lower() in event["name"].lower()]

    def fetch_mentorship(self, query: str) -> List[Dict]:
        return [mentor for mentor in self.mentorship_data if query.lower() in mentor["expertise"].lower()]

api = MockAPI()

# Bias detection
def detect_bias(user_input: str) -> bool:
    bias_keywords = ["men are better", "women can't", "only men", "weak women"]
    return any(keyword in user_input.lower() for keyword in bias_keywords)

def speak(text):
    if tts_enabled and engine:
        try:
            print(f"Speaking: {text}")
            engine.say(text)
            engine.runAndWait()
            return True
        except Exception as e:
            print(f"Error in text-to-speech: {e}")
            return False
    return False

def get_gemini_response(prompt, context: List[Dict] = None):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        if context:
            prompt = f"Conversation history: {json.dumps(context)}\nUser query: {prompt}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error: {e}")
        return "Sorry, I couldn’t process that. Try again or contact support."

@app.route('/')
def home():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        session['context'] = []
    return render_template('index1.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        session['context'] = []

    user_message = request.json['message']
    speak_response = request.json.get('speak', False)
    context = session['context']

    # Log interaction
    logging.basicConfig(filename='asha_ai.log', level=logging.INFO)
    logging.info(f"Session {session['session_id']} - User: {user_message}")

    # Bias check
    if detect_bias(user_message):
        response = "I noticed a potentially biased query. Let’s focus on empowering women’s careers! Ask about jobs, events, or mentorship."
        context.append({"user": user_message, "bot": response})
        session['context'] = context
        logging.warning(f"Session {session['session_id']} - Bias detected in input: {user_message}")
    else:
        # Handle specific queries
        if "job" in user_message.lower() or "career" in user_message.lower():
            jobs = api.fetch_jobs(user_message)
            if jobs:
                response = "Here are some job listings:\n" + "\n".join(
                    [f"- {job['title']} at {job['company']} ({job['location']}, {job['type']})" for job in jobs]
                )
            else:
                response = "No jobs found. Try a different role or industry!"
        elif "event" in user_message.lower() or "workshop" in user_message.lower():
            events = api.fetch_events(user_message)
            if events:
                response = "Upcoming events:\n" + "\n".join(
                    [f"- {event['name']} on {event['date']} ({event['location']})" for event in events]
                )
            else:
                response = "No events found. Check back later!"
        elif "mentor" in user_message.lower() or "guidance" in user_message.lower():
            mentors = api.fetch_mentorship(user_message)
            if mentors:
                response = "Available mentorship programs:\n" + "\n".join(
                    [f"- {mentor['mentor']} ({mentor['expertise']}, {mentor['availability']})" for mentor in mentors]
                )
            else:
                response = "No mentorship programs found. Try another area!"
        else:
            response = get_gemini_response(user_message, context)

        context.append({"user": user_message, "bot": response})
        session['context'] = context

    if speak_response and tts_enabled:
        speak(response)

    return jsonify({'response': response, 'speech_successful': speak_response and tts_enabled})

@app.route('/speak_text', methods=['POST'])
def speak_text():
    text = request.json.get('text', '')
    success = speak(text)
    return jsonify({'success': success})

@app.route('/feedback', methods=['POST'])
def provide_feedback():
    feedback = request.json.get('feedback', '')
    logging.info(f"Session {session['session_id']} - Feedback: {feedback}")
    return jsonify({'response': "Thanks for your feedback! We’re improving daily."})

if __name__ == "__main__":
    if not os.path.exists('templates'):
        os.makedirs('templates')
    app.run(debug=True)


