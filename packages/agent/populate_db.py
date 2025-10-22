import os
import re
import firebase_admin
from firebase_admin import credentials, firestore
import datetime

# --- Common Stop Words (you can expand this list) ---
STOP_WORDS = set([
    "a", "an", "the", "is", "are", "was", "were", "be", "being", "been",
    "of", "at", "in", "on", "to", "for", "with", "about", "by", "do", "you"
])

# --- Initialization ---

os.environ['FIRESTORE_EMULATOR_HOST'] = 'localhost:8080'
cred = credentials.Certificate("serviceAccountKey.json") 
firebase_admin.initialize_app(cred)
db = firestore.client()
if os.getenv('USE_EMULATOR', 'true') == 'true':
    os.environ['FIRESTORE_EMULATOR_HOST'] = 'localhost:8080'
    print("Connected to Firestore Emulator")


def generate_keywords(text: str) -> list[str]:
    """
    Processes a text string to extract a list of unique, significant keywords.
    - Converts to lowercase
    - Removes punctuation
    - Splits into words
    - Removes common "stop words"
    """
    # Convert to lowercase and remove punctuation
    text = re.sub(r'[^\w\s]', '', text.lower())
    # Split into words and filter out stop words and short words
    keywords = [word for word in text.split() if word not in STOP_WORDS and len(word) > 2]
    # Return a list of unique keywords
    return list(set(keywords))

def add_qa_to_knowledge_base(question_text, answer_text, category="general"):
    """
    Adds a new question and answer pair to the 'knowledge_base',
    including generated keywords for searching.
    """
    print(f"\n📝 Adding: '{question_text}'")
    
    knowledge_base_ref = db.collection('knowledge_base')
    
    # Check if the exact question already exists
    if knowledge_base_ref.where('question_text', '==', question_text).limit(1).get():
        print("🟡 Question already exists. Skipping.")
        return

    # Generate keywords from the question
    keywords = generate_keywords(question_text)
    print(f"   -> Generated Keywords: {keywords}")

    # Create the new document data
    new_qa_document = {
        'question_text': question_text,
        'answer_text': answer_text,
        'question_keywords': keywords,
        'category': category,
        'usage_count': 0,
        'created_at': datetime.datetime.now(datetime.timezone.utc),
        'flagged_for_review': False,
        'schema_version': 2
    }

    try:
        # Add the new document
        doc_ref = knowledge_base_ref.add(new_qa_document)
        print(f"✅ Successfully added Q&A with document ID: {doc_ref[1].id}")
    except Exception as e:
        print(f"❌ An error occurred: {e}")


# --- Main execution block to add your data ---
if __name__ == "__main__":
    add_qa_to_knowledge_base(
        "When is the opening time of the saloon?", 
        "We are open every day from 11 am.",
        "business_hours"
    )
    add_qa_to_knowledge_base(
        "Do you do color treatments?", 
        "Yes, we specialize in black and brown color treatments.",
        "services"
    )
    add_qa_to_knowledge_base(
        "How much does a haircut cost?",
        "A standard haircut costs ₹500.",
        "pricing"
    )
    print("\n✨ Database population script finished.")