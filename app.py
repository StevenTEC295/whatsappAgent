from flask import Flask, request, Response
from twilio.rest import Client
from google.cloud import dialogflow
import os
from google.oauth2 import service_account

app = Flask(__name__)

# Configuración de Twilio (usar variables de entorno)
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = 'whatsapp:+14155238886'  # Número sandbox de Twilio

# Configuración de DialogFlow
DIALOGFLOW_PROJECT_ID = os.getenv('DIALOGFLOW_PROJECT_ID')
LANGUAGE_CODE = 'es'

# Cliente de DialogFlow
credentials = service_account.Credentials.from_service_account_info({
    "type": "service_account",
    "project_id": os.getenv('DIALOGFLOW_PROJECT_ID'),
    "private_key_id": os.getenv('PRIVATE_KEY_ID'),
    "private_key": os.getenv('PRIVATE_KEY').replace("\\n", "\n"),
    "client_email": os.getenv('CLIENT_EMAIL'),
    "client_id": os.getenv('CLIENT_ID'),
    "auth_uri": os.getenv('AUTH_URI'),
    "token_uri": os.getenv('TOKEN_URI'),
    "auth_provider_x509_cert_url": os.getenv('AUTH_PROVIDER'),
    "client_x509_cert_url": os.getenv('CERT_URL'),
    "universe_domain": os.getenv('UNIVERSE_DOMAIN')
  
}
)
session_client = dialogflow.SessionsClient(credentials=credentials)

@app.route('/webhook', methods=['POST'])
def webhook():
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    # Obtener mensaje entrante de Twilio
    incoming_msg = request.values.get('Body', '').strip()
    sender_phone = request.values.get('From', '')
    print(sender_phone)
    
    print(f"Mensaje recibido de {sender_phone}: {incoming_msg}")
    
    try:
        # Procesar mensaje con DialogFlow
        dialogflow_response = detect_intent_texts(
            DIALOGFLOW_PROJECT_ID, 
            sender_phone, 
            incoming_msg, 
            LANGUAGE_CODE
        )
        print("Respuesta de DialogFlow:", dialogflow_response)
        
        # Preparar respuesta TwiML para Twilio
        message = client.messages.create(
        from_='whatsapp:+14155238886',
        body=dialogflow_response,   
        to="whatsapp:+{}".format(sender_phone.replace("whatsapp: ", ""))  # Eliminar "whatsapp:" del número de teléfono
        )
        print("Mensaje enviado:", message.body)
        return Response(str(message), mimetype='application/xml')
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return Response(str(e), status=500, mimetype='text/plain')
def detect_intent_texts(project_id, session_id, text, language_code):
    """Devuelve el resultado de la detección de intención usando DialogFlow"""
    session = session_client.session_path(project_id, session_id)
    
    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)
    
    response = session_client.detect_intent(
        request={"session": session, "query_input": query_input}
    )
    
    return response.query_result.fulfillment_text

if __name__ == '__main__':
    app.run(debug=True, port=8000)
