from flask import Flask
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configure API keys
    app.config['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
    app.config['TELNYX_API_KEY'] = os.getenv('TELNYX_API_KEY')
    app.config['TELNYX_SENDER_ID'] = os.getenv('TELNYX_SENDER_ID')
    app.config['TELNYX_PHONE_NUMBER'] = os.getenv('TELNYX_PHONE_NUMBER')

def run_app():
    app = create_app()
    app.run(debug=True, port=5001)

if __name__ == '__main__':
    run_app() 