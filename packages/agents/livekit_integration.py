import os
import sys
import asyncio
from datetime import datetime, timezone
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Fix Windows asyncio multiprocessing issues
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    RoomInputOptions,
    WorkerOptions,
    cli,
    function_tool,
    RunContext,
)
from livekit.plugins import (
    noise_cancellation,
    silero,
)

load_dotenv(".env.local")

# --- Firebase Initialization (Updated) ---
cred = credentials.Certificate("serviceAccountKey.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
# Use the ASYNC client for a non-blocking connection
db = firestore.client()
if os.getenv("USE_EMULATOR", "true") == "true":
    os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
    print("Connected to Firestore Emulator")


# --- Assistant ---
class Assistant(Agent):
    def __init__(self, db_client, instructions: str):
        super().__init__(instructions=instructions)
        self.db = db_client

    # In the Assistant class in livekit_integration.py

    @function_tool
    async def create_help_request(self, context: RunContext, question: str):
        """
        Use this tool ONLY when you cannot find the answer to a user's question
        in the provided KNOWLEDGE BASE. This tool will escalate the question to a human supervisor.
        """
        print(f"✍️ Escalating question via function tool: '{question}'")

        request_ref = self.db.collection('help_requests').document()
        answer_received_event = asyncio.Event()
        answer_text = ""

        def on_snapshot(doc_snapshot, changes, read_time):
            nonlocal answer_text
            for doc in doc_snapshot:
                if doc.exists:
                    data = doc.to_dict()
                    if data.get("status") == "Resolved" and data.get("supervisor_response"):
                        # This is where we get the answer and log it
                        answer_text = data["supervisor_response"]
                        print("\n✅✅✅ Supervisor responded!! ✅✅✅\n") # Your requested log message
                    if not answer_received_event.is_set():
                        answer_received_event.set()
                    break
    
        listener = request_ref.on_snapshot(on_snapshot)

        try:
            request_ref.set({
                'customer_id': "test-user-123",
                'question_text': question,
                'status': 'pending',
                'received_at': datetime.now(timezone.utc),
                'supervisor_response': None,
            })
            print(f"📄 Help request {request_ref.id} created. Waiting for supervisor...")
            await context.session.say("I couldn't find that in my knowledge base. Let me check with my supervisor, please wait a moment.")
            await asyncio.wait_for(answer_received_event.wait(), timeout=300.0)
        
            # The agent now speaks the supervisor's answer directly
            await context.session.say(f"I have an answer from my supervisor. They said: {answer_text}")
            return "Successfully relayed the supervisor's verbatim answer."

        except asyncio.TimeoutError:
            print("⌛️ Timed out waiting for a supervisor answer.")
            await context.session.say("I'm sorry, my supervisor is taking longer than expected to respond. Please try again later.")
            return "Timed out waiting for an answer."
        except Exception as e:
            print(f"❌ Error in help request tool: {e}")
            return "I'm having trouble with my internal tools right now."
        finally:
            listener.unsubscribe()
            print(f"👂 Stopped listening to request {request_ref.id}")

def prewarm(proc: JobProcess):
    """Pre-load models for faster startup."""
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # --- Fetch Knowledge Base ---
    knowledge_base_str = ""
    try:
        print("📚 Fetching knowledge base from Firestore...")
        # Use the async stream() for non-blocking fetch
        docs_stream = db.collection("knowledge_base").stream()
        qa_pairs = [
            f"Q: {doc.get('question_text')}\nA: {doc.get('answer_text')}"
            for doc in docs_stream
        ]
        if not qa_pairs:
            knowledge_base_str = "No information is available in the knowledge base."
        else:
            knowledge_base_str = "\n".join(qa_pairs)
        print("✅ Knowledge base fetched.")
    except Exception as e:
        print(f"❌ Error fetching knowledge base: {e}")
        knowledge_base_str = "Error fetching knowledge base."

    # --- Construct the Dynamic Prompt ---
    dynamic_instructions = f"""
You are a friendly customer service agent for COLORS HAIR SALON.

You MUST follow these steps for EVERY user question, without exception:
Step 1: Carefully search the KNOWLEDGE BASE below to find an answer to the user's question.
Step 2: Internally, think to yourself: "Did I find a direct answer in the knowledge base?".
Step 3: If the answer is YES, you must provide ONLY that answer to the user. Do not mention the knowledge base.
Step 4: If the answer is NO, you absolutely MUST use the 'create_help_request' tool. Do not apologize or make up an answer.

This is your only source of information.

--- KNOWLEDGE BASE ---
{knowledge_base_str}
--- END KNOWLEDGE BASE ---
"""

    session = AgentSession(
        llm="openai/gpt-4o-mini",
        stt="assemblyai/universal-streaming:en",
        tts="cartesia/sonic-2:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        vad=ctx.proc.userdata["vad"],
        turn_detection="vad",
    )

    agent = Assistant(db_client=db, instructions=dynamic_instructions)
    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC()
        ),
    )
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))