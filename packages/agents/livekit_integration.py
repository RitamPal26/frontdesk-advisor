# packages/agents/livekit_integration.py
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import silero, noise_cancellation

load_dotenv(".env.local")

class FrontdeskAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="You are a friendly customer service agent for COLORS Salon. Greet customers warmly, ask how their day was and ask what their question is and chat with them."
        )

async def entrypoint(ctx: agents.JobContext):
    # Use LiveKit Inference - no extra API keys needed
    session = AgentSession(
        stt="assemblyai/universal-streaming:en",
        llm="openai/gpt-4.1-mini",
        tts="cartesia/sonic-2",
        vad=silero.VAD.load(),
    )
    
    agent = FrontdeskAgent()
    
    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
    
    # Generate initial greeting
    await session.generate_reply(
        instructions="Greet the customer warmly and ask how you can help them today."
    )

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
