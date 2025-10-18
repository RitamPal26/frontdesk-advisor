import firebase_admin
from firebase_admin import credentials, firestore
import datetime

# --- Initialization ---
# Use the service account key you downloaded
cred = credentials.Certificate("serviceAccountKey.json") 
firebase_admin.initialize_app(cred)

# Get a reference to the Firestore database
db = firestore.client()

print("✅ Successfully connected to Firestore.")

# --- Create Sample Data ---
# This is a sample of the data you'll create when the AI needs help
sample_request = {
    'customer_id': 'simulated_customer_123',
    'question_text': 'Do you offer student discounts?',
    'status': 'Pending',
    'received_at': datetime.datetime.now(datetime.timezone.utc)
}

# --- Write Data to Firestore ---
try:
    # Add a new document to the 'help_requests' collection
    # The .add() method will automatically generate a unique ID for the document
    update_time, doc_ref = db.collection('help_requests').add(sample_request)
    
    print(f"📝 Successfully added help request with ID: {doc_ref.id}")
    print(f"Timestamp: {update_time}")

except Exception as e:
    print(f"❌ An error occurred: {e}")