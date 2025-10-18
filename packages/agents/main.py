import os
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import time

# --- Initialization ---
os.environ['FIRESTORE_EMULATOR_HOST'] = 'localhost:8080'

# Use the service account key you downloaded
cred = credentials.Certificate("serviceAccountKey.json") 
firebase_admin.initialize_app(cred)

# Get a reference to the Firestore database
db = firestore.client()

if os.getenv('USE_EMULATOR', 'true') == 'true':
    os.environ['FIRESTORE_EMULATOR_HOST'] = 'localhost:8080'
    print("Connected to Firestore Emulator")

# --- Create Sample Data ---
def handle_incoming_question(question_text):
    print(f"\n📞 Incoming question: '{question_text}'")
    
    # 1. Query the knowledge_base first
    knowledge_base_ref = db.collection('knowledge_base')
    query = knowledge_base_ref.where('question', '==', question_text).limit(1)
    results = list(query.stream()) # Use list() to execute the query and get results

    # 2. If an answer is found, use it
    if len(results) > 0:
        learned_answer = results[0].to_dict().get('answer')
        print(f"🤖 AI Response (from knowledge base): '{learned_answer}'")
        return

    # 3. If no answer is found, create a help request
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


# --- Main execution loop to simulate calls ---
if __name__ == "__main__":
    # Test with the question we already taught the AI
    handle_incoming_question("Do you offer student discounts?")
    
    time.sleep(2) # Pause for clarity in output
    
    # Test with a new, unknown question
    handle_incoming_question("Do you do color treatments?")