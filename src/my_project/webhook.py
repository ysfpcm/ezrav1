# webhook.py
from http import client
import json
import requests
from flask import Blueprint, request, jsonify, current_app
import openai
# Define the blueprint
webhook_bp = Blueprint('webhook', __name__)

# In-memory storage for demonstration (use a database in production)
last_received_message = {}

@webhook_bp.route("/", methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "message": "Webhook server is running"
    })

@webhook_bp.route("/sms", methods=['POST'])
def sms_handler():
    """Handle incoming SMS messages."""
    print("\n========= NEW SMS MESSAGE =========")
    
    try:
        # Get the JSON payload from the webhook
        data = request.get_json()
        print("Raw webhook data:", json.dumps(data, indent=2))

        # Check if it's an incoming message event
        event_type = data.get('data', {}).get('event_type', '')
        
        if event_type == 'message.received':
            payload = data.get('data', {}).get('payload', {})
            incoming_msg = payload.get('text', '').strip()
            sender_phone = payload.get('from', {}).get('phone_number', '')
            
            print(f"\n📱 From: {sender_phone}")
            print(f"📝 Message: {incoming_msg}")
            
            # Store the message for debugging or retrieval via GET
            last_received_message['from'] = sender_phone
            last_received_message['message'] = incoming_msg
            
            # Generate a response from OpenAI
            response_text = process_incoming_message(incoming_msg)
            
            # Send the response back to the sender
            send_sms_response(sender_phone, response_text)
            
            return jsonify({
                "status": "success",
                "message": "SMS received and response sent",
                "received_text": incoming_msg,
                "from_number": sender_phone
            })
        
        # Return ignored status for non-message.received events
        return jsonify({
            "status": "ignored",
            "message": f"Ignored event type: {event_type}"
        })
        
    except Exception as e:
        print(f"❌ Error processing SMS: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

def send_sms_response(phone_number, message):
    """Send an SMS response using the Telnyx API."""
    telnyx_api_key = current_app.config.get('TELNYX_API_KEY')
    messaging_profile_id = current_app.config.get('TELNYX_SENDER_ID')
    from_number = current_app.config.get('TELNYX_PHONE_NUMBER')
    
    url = "https://api.telnyx.com/v2/messages"
    headers = {
        "Authorization": f"Bearer {telnyx_api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "from": from_number,
        "to": phone_number,
        "text": message,
        "messaging_profile_id": messaging_profile_id
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response_data = response.json()
    
    if response.status_code >= 400:
        print(f"❌ Failed to send SMS: {response_data}")
    else:
        print(f"✅ SMS sent successfully: {response_data}")
    
    return response_data

def process_incoming_message(incoming_msg):
    """Generate a response to the incoming message using OpenAI ChatCompletion API."""
    openai.api_key = current_app.config.get('OPENAI_API_KEY')
    
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": incoming_msg
            }
        ]
    )
    
    # Access the response content correctly
    answer = response.choices[0].message.content.strip()
    print(f"🤖 OpenAI Response: {answer}")
    
    return answer

@webhook_bp.errorhandler(405)
def method_not_allowed(e):
    """Handle unsupported methods."""
    return jsonify({
        "status": "error",
        "message": "Method Not Allowed"
    }), 405
