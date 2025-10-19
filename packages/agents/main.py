import os
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import time
from livekit_integration import LiveKitAgentServer

# --- Initialization ---
os.environ['FIRESTORE_EMULATOR_HOST'] = 'localhost:8080'
cred = credentials.Certificate("serviceAccountKey.json") 
firebase_admin.initialize_app(cred)
db = firestore.client()

if os.getenv('USE_EMULATOR', 'true') == 'true':
    os.environ['FIRESTORE_EMULATOR_HOST'] = 'localhost:8080'
    print("Connected to Firestore Emulator")


def handle_incoming_question(question_text):
    print(f"\n📞 Incoming question: '{question_text}'")
    
    knowledge_base_ref = db.collection('knowledge_base')
    query = knowledge_base_ref.where('question', '==', question_text).limit(1)
    results = list(query.stream())

    if len(results) > 0:
        learned_answer = results[0].to_dict().get('answer')
        print(f"🤖 AI Response (from knowledge base): '{learned_answer}'")
        return

    print("🤖 AI Response: 'I don't know that one. Let me check with my supervisor...'")
    
    help_request = {
        'customer_id': 'simulated_customer_123',
        'question_text': question_text,
        'status': 'Pending',
        'received_at': datetime.datetime.now(datetime.timezone.utc)
    }

    try:
        update_time, doc_ref = db.collection('help_requests').add(help_request)
        print(f"📝 Successfully created help request with ID: {doc_ref.id}")
    except Exception as e:
        print(f"❌ An error occurred while creating help request: {e}")

async def main():
    # Create an instance of our server, passing our business logic function as the callback
    server = LiveKitAgentServer(on_question_received=handle_incoming_question)
    
    # Start the server
    await server.start()

if __name__ == "__main__":    
    try:
        handle_incoming_question("Do you offer student discounts?")
        time.sleep(2)
        handle_incoming_question("Do you do color treatments?")
    finally:
        # Close the Firestore client connection
        db.close()
        print("\n✅ Closed Firestore connection")
