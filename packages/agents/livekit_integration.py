import os
import asyncio
from datetime import datetime, timezone
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    openai,
    cartesia,
    deepgram,
    noise_cancellation,
    silero,
)
from livekit.plugins import openai
from livekit.plugins.turn_detector.english import EnglishModel
from livekit.agents import AgentSession

load_dotenv(".env.local")

# --- Initialization ---

os.environ['FIRESTORE_EMULATOR_HOST'] = 'localhost:8080'
cred = credentials.Certificate("serviceAccountKey.json") 
firebase_admin.initialize_app(cred)
db = firestore.client()
if os.getenv('USE_EMULATOR', 'true') == 'true':
    os.environ['FIRESTORE_EMULATOR_HOST'] = 'localhost:8080'
    print("Connected to Firestore Emulator")


# ENHANCED: --- This is now your powerful Frontdesk Agent ---
class Assistant(Agent):
    def __init__(self, db_client, instructions: str) -> None:
        super().__init__(instructions=instructions)
        self.db = db_client # ADDED: Store the database client

    # ADDED: The core logic for escalating to a supervisor
    def create_help_request(self, customer_id: str, question: str):
        print(f"✍️ Escalating question to supervisor: '{question}'")
        try:
            self.db.collection('help_requests').add({
                'customer_id': customer_id,
                'question_text': question,
                'status': 'Pending',
                'received_at': datetime.now(timezone.utc),
            })
            print("✅ Help request created in Firestore.")
            return "Let me check with my supervisor and get back to you shortly."
        except Exception as e:
            print(f"❌ Error creating help request: {e}")
            return "I'm having some trouble right now, please call back later."

    # ADDED: This method will contain the main conversation loop
    async def start(self, session: AgentSession):
        # Start listening to transcriptions from the user
        async for text in session.stt.stream():
            print(f"User said: {text}")

            # Get the LLM's response based on our dynamic instructions
            llm_stream = await session.llm.chat(text, instructions=self.instructions)

            response_text = ""
            async for chunk in llm_stream:
                response_text += chunk.text
                
            print(f"LLM RAW TEXT: '[{response_text.strip()}]'")

            # Check for our special escalation keyword
            if "Please hold on while I get my supervisor" in response_text:
                escalation_message = self.create_help_request(
                    customer_id="live_customer_123", # You can make this dynamic later
                    question=text
                )
                await session.say(escalation_message)
            else:
                await session.say(response_text)


async def entrypoint(ctx: agents.JobContext):
    # ENHANCED: --- Fetch Knowledge Base before starting ---
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

    # ENHANCED: --- Construct the Dynamic Prompt ---
    dynamic_instructions = f"""
    You are a friendly and helpful customer service agent for COLORS HAIR SALON. Greet the customer with a warm welcome and ask how you can assist them today.
    Your primary goal is to answer questions based ONLY on the information provided below.

    --- KNOWLEDGE BASE ---
    {knowledge_base_str}
    --- END KNOWLEDGE BASE ---

    Follow these rules STRICTLY:
    1. Answer if Known: If the user's question can be answered using the knowledge base, provide the answer.
    2. Escalate if Unknown: If the question CANNOT be answered, you MUST respond with ONLY the exact phrase: Please hold on while I get my supervisor.
    3. Do Not Guess: Never make up answers or use external information.
    """

    session = AgentSession(
        llm=openai.LLM.with_cerebras(
        model="llama-3.3-70b",
        ),
        stt=deepgram.STT(model="nova-2", language="en"),
        tts=cartesia.TTS(model="sonic-2", voice="f786b574-daa5-4673-aa0c-cbe3e8534c02"),
        vad=silero.VAD.load(),
        turn_detection=EnglishModel(),
    )
    
    # ENHANCED: Initialize our agent with the db client and dynamic instructions
    agent = Assistant(db_client=db, instructions=dynamic_instructions)

    # The start method of our agent will be called here, starting the main loop
    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(), 
        ),
    )

    # You can remove the old greeting, as the agent now waits for the user to speak first
    # await session.generate_reply( ... )

    # The agent's `start` method will keep running, so we just wait
    await asyncio.sleep(3600) # Keep the agent alive for an hour, for example


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))