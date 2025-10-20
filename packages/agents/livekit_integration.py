import os
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import silero, noise_cancellation

load_dotenv(".env.local")

# FB: 1. --- Initialize Firebase Admin SDK ---
try:
    # Ensure serviceAccountKey.json is in your project directory
    if not firebase_admin._apps:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        print("✅ Firebase App initialized.")
except Exception as e:
    print(f"❌ Error initializing Firebase App: {e}")
    exit()

db = firestore.client()

# FB: 2. --- Connect to Local Emulators ---
if os.environ.get('USE_FIREBASE_EMULATOR'):
    print("🔌 Connecting to Firebase Emulator...")
    os.environ['FIRESTORE_EMULATOR_HOST'] = 'localhost:8080'
    print("🔌 Connected to Firestore Emulator at localhost:8080")


class FrontdeskAgent(Agent):
    def __init__(self, db_client, instructions: str):
        super().__init__(instructions=instructions)
        self.db = db_client

    def create_help_request(self, customer_id: str, question: str):
        print(f"✍️ Escalating question to supervisor: '{question}'")
        try:
            help_requests_ref = self.db.collection('help_requests')
            help_requests_ref.add({
                'customer_id': customer_id,
                'question_text': question,
                'status': 'Pending',
                'received_at': datetime.now(timezone.utc),
                'resolved_at': None,
                'supervisor_response': '',
                'addedToKnowledgeBase': False,
            })
            print("✅ Help request created in Firestore.")
            return "Let me check with my supervisor and get back to you shortly."
        except Exception as e:
            print(f"❌ Error creating help request: {e}")
            return "I'm having trouble connecting to my system right now, please call back later."

async def entrypoint(ctx: agents.JobContext):
    # --- 1. Fetch Knowledge Base ---
    knowledge_base_str = ""
    try:
        print("📚 Fetching knowledge base from Firestore...")
        docs = db.collection('knowledge_base').stream()
        qa_pairs = [f"Q: {doc.get('question_text')}\nA: {doc.get('answer_text')}" for doc in docs]
        
        if not qa_pairs:
            knowledge_base_str = "No information is available in the knowledge base."
        else:
            knowledge_base_str = "\n".join(qa_pairs)
        print("✅ Knowledge base fetched.")
    except Exception as e:
        print(f"❌ Error fetching knowledge base: {e}")
        knowledge_base_str = "Error fetching knowledge base."

    # --- 2. Construct Dynamic Prompt ---
    dynamic_instructions = f"""
    You are a friendly and helpful customer service agent for COLORS Hair Salon. Your primary goal is to answer customer questions accurately based ONLY on the information provided below.

    --- KNOWLEDGE BASE ---
    {knowledge_base_str}
    --- END KNOWLEDGE BASE ---

    Follow these rules STRICTLY:
    1. Check the Knowledge Base: Before answering, review the information provided above.
    2. Answer if Known: If the user's question can be answered using the knowledge base, provide the answer in a friendly tone.
    3. Escalate if Unknown: If the user's question CANNOT be answered from the knowledge base, or if you are unsure, you MUST respond with ONLY the exact phrase: NEEDS_SUPERVISOR
    4. Do Not Guess: Never make up answers or use information from outside the provided knowledge base. If it's not written above, you don't know it.
    """
    
    session = AgentSession(
        stt="assemblyai/universal-streaming:en",
        llm="openai/gpt-4.1-mini",
        tts="cartesia/sonic-2",
        vad=silero.VAD.load(),
    )
    
    # The agent is initialized with our detailed instructions here
    agent = FrontdeskAgent(db_client=db, instructions=dynamic_instructions)
    
    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
    
    # --- Main interaction loop (simplified example) ---
    customer_question = "When is the salon open?"
    
    # FIXED: The chat() method takes the user's message as the main argument.
    # The instructions we set when creating the agent are used automatically.
    llm_stream = session.llm.chat(customer_question)

    ai_response_text = ""
    async for chunk in llm_stream:
        ai_response_text += chunk.text

    # Now, check the complete text response
    if "NEEDS_SUPERVISOR" in ai_response_text:
        response_to_customer = agent.create_help_request(
            customer_id="simulated_customer_789",
            question=customer_question
        )
        await session.say(response_to_customer)
    else:
        await session.say(ai_response_text)

if __name__ == "__main__":
    os.environ['USE_FIREBASE_EMULATOR'] = 'true'
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))