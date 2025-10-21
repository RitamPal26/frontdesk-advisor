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

# --- Firebase Initialization ---
cred = credentials.Certificate("serviceAccountKey.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()
if os.getenv("USE_EMULATOR", "true") == "true":
    os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
    print("Connected to Firestore Emulator")


# --- Assistant ---
class Assistant(Agent):
    def __init__(self, db_client, instructions: str):
        super().__init__(instructions=instructions)
        self.db = db_client

    @function_tool
    async def create_help_request(self, context: RunContext, question: str):
        """
        Use this tool ONLY when you cannot find the answer to a user's question
        in the provided KNOWLEDGE BASE. This tool will escalate the question to a human supervisor.

        Args:
            question: The user's original question that you could not answer.
        """
        print(f"✍️ Escalating question via function tool: '{question}'")
        customer_id = "test-user-123"
        try:
            self.db.collection('help_requests').add({
                'customer_id': customer_id,
                'question_text': question,
                'status': 'Pending',
                'received_at': datetime.now(timezone.utc),
            })
            print("✅ Help request created in Firestore.")
            return "I couldn't find a specific answer for that, but I've forwarded your question to my supervisor. They will get back to you soon."
        except Exception as e:
            print(f"❌ Error creating help request: {e}")
            return "I'm having some trouble with my internal tools right now. Please try again later."


def prewarm(proc: JobProcess):
    """Pre-load models for faster startup."""
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # --- Fetch Knowledge Base ---
    knowledge_base_str = ""
    try:
        print("📚 Fetching knowledge base from Firestore...")
        docs = db.collection("knowledge_base").stream()
        qa_pairs = [
            f"Q: {doc.get('question_text')}\nA: {doc.get('answer_text')}"
            for doc in docs
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
Your primary goal is to answer questions based ONLY on the information in the KNOWLEDGE BASE.

--- KNOWLEDGE BASE ---
{knowledge_base_str}
--- END KNOWLEDGE BASE ---

For every user question, you must follow this process:
1. Analyze the question against the KNOWLEDGE BASE.
2. If the answer is in the KNOWLEDGE BASE, provide it to the user.
3. If the answer is NOT in the KNOWLEDGE BASE, you MUST use the 'create_help_request' tool to escalate. DO NOT make up an answer.

Keep your responses concise and conversational, avoiding complex formatting or punctuation.
"""

    # Create session
    session = AgentSession(
        llm="openai/gpt-4.1-mini",
        stt="assemblyai/universal-streaming:en",
        tts="cartesia/sonic-2:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        vad=ctx.proc.userdata["vad"],
        turn_detection="vad",
    )

    # Create agent
    agent = Assistant(db_client=db, instructions=dynamic_instructions)

    # Start the session
    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC()
        ),
    )

    # Connect to the room
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
