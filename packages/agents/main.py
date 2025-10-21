import os
import re
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
from livekit_integration import LiveKitAgentServer 

# --- Common Stop Words (must be identical to the populator script) ---
STOP_WORDS = set([
    "a", "an", "the", "is", "are", "was", "were", "be", "being", "been",
    "of", "at", "in", "on", "to", "for", "with", "about", "by", "do", "you"
])

# --- Initialization ---
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
except FileNotFoundError:
    print("❌ Error: serviceAccountKey.json not found.")
    exit()

db = firestore.client()

# --- Connect to Emulator ---
os.environ['FIRESTORE_EMULATOR_HOST'] = 'localhost:8080'
print("🔌 Connected to Firestore Emulator at localhost:8080")

def generate_keywords(text: str) -> list[str]:
    """
    Processes a text string to extract keywords. This MUST be identical
    to the function in the populate_db.py script.
    """
    text = re.sub(r'[^\w\s]', '', text.lower())
    keywords = [word for word in text.split() if word not in STOP_WORDS and len(word) > 2]
    return list(set(keywords))

def handle_incoming_question(question_text: str):
    """
    Receives a question, searches the knowledge base using keywords,
    and decides on a response or escalation.
    """
    print(f"\n📞 Incoming question: '{question_text}'")
    
    # 1. Generate keywords from the user's question
    search_keywords = generate_keywords(question_text)
    print(f"   -> Searching with keywords: {search_keywords}")
    
    if not search_keywords:
        print("🤖 AI Response: 'I'm sorry, I didn't understand the question. Could you rephrase?'")
        return # Or escalate

    knowledge_base_ref = db.collection('knowledge_base')
    query = knowledge_base_ref.where('question_keywords', 'array-contains-any', search_keywords)
    results = list(query.stream())
    
    best_match = None
    highest_score = 0
    
    for doc in results:
        doc_data = doc.to_dict()
        doc_keywords = doc_data.get('question_keywords', [])
        # Score is the number of matching keywords
        score = len(set(search_keywords) & set(doc_keywords))
        
        if score > highest_score:
            highest_score = score
            best_match = doc_data

    # Confidence is the ratio of matched keywords to search keywords
    confidence = highest_score / len(search_keywords) if search_keywords else 0
    print(f"   -> Best match found with confidence: {confidence:.2f}")

    if confidence > 0.6: # High confidence threshold
        answer = best_match.get('answer_text', "I found an answer but could not retrieve it.")
        print(f"🤖 AI Response (from knowledge base): '{answer}'")
        # Here you would send the answer back to the user via LiveKit
        return answer
    
    # Low confidence -> Escalate to human
    print("🤖 AI Response: 'I'm not sure about that. Let me check with my supervisor...'")
    create_help_request(question_text)
    return "Let me check with my supervisor."


def create_help_request(question_text):
    """Creates a help request document in Firestore."""
    help_request = {
        'customer_id': 'simulated_customer_123',
        'question_text': question_text,
        'status': 'pending', # Status can be: pending, assigned, resolved
        'created_at': datetime.datetime.now(datetime.timezone.utc),
        'version': 1,
        'schema_version': 1
    }
    try:
        _, doc_ref = db.collection('help_requests').add(help_request)
        print(f"📝 Successfully created help request with ID: {doc_ref.id}")
    except Exception as e:
        print(f"❌ An error occurred while creating help request: {e}")

async def main():
    """Starts the LiveKit Agent Server."""
    print("\n🚀 Starting LiveKit Agent Server...")
    # Create an instance of our server, passing our business logic function
    server = LiveKitAgentServer(on_question_received=handle_incoming_question)
    await server.start()

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n shutting down server.")