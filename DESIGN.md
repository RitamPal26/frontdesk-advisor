## High-Level Architecture

"This is an AI voice agent for customer relations working in COLORS HARI SALON. The `supervisor-ui` provides an admin web interface. It connects to Firebase (`functions`) for data and state management. The core voice logic is handled by the Python `agent` package, which communicates using LiveKit."

`[Supervisor-UI (Next.js)] <-> [Firebase (Functions/Firebase)] <-> [agent (Python/LiveKit)]`

***

## Component Breakdown

* ### `supervisor-ui/` (Next.js)
    * **Purpose:** The admin panel for supervisors to monitor help_requests and see the resolved/unresolved issues.
    * **Key Features:** Real-time list updated every time the agent needs help from the supervisor.
    * **Tech:** Next.js, pnpm, Firebase SDK, typescript.

* ### `functions/` (Firebase Emulators)
    * **Purpose:** The serverless backend for the project.
    * **Key Functions:** has knowledge_base and help_requests collections for the agent to answer the questions live.
    * **Database:** Using Firestore to store user data, queries and learn the answers.

* ### `agent/` (Python)
    * **Purpose:** The core AI voice agent.
    * **Logic:** Uses LiveKit agent(https://github.com/livekit/agent) to simulate an AI Agent that can handle queries about the COLORS HAIR SALON.
    * **Key Tech:** LiveKit agent, Python.

***

## Database Schema (Firestore)

The project relies on two main collections in Firestore:

### `knowledge_base`
This collection acts as the agent's long-term memory. The agent queries this collection to find answers to customer questions.

* **Document ID:** (Auto-generated)
* **Fields:**
    * `answer_text` (string): The pre-written answer the agent will speak.
        * *Example: "We are a saloon, please ask relevant questions."*
    * `category` (string): A category for the query.
        * *Example: "miscellaneous"*
    * `created_at` (timestamp): When this entry was added.
    * `flagged_for_review` (boolean): `true` if a supervisor needs to verify this answer.
    * `question_keywords` (array): A list of keywords to help the agent find this answer.
        * *Example: ["weather", "today"]*
    * `question_text` (string): The original question this document answers.
        * *Example: "What is the weather today?"*
    * **`schema_version`** (number): Tracks the structure of this document. This is for     maintenance, so if you ever add or remove fields, you can change the version to know which documents have the new structure.
        * *Example: 2*
    * **`usage_count`** (number): A counter for how many times the agent has successfully used this answer. This is useful for analytics to see which answers are most popular or helpful.
        * *Example: 2*

### `help_requests`
This collection is a "ticket" system. When the agent fails to find an answer in the `knowledge_base`, it creates a new document here for a human supervisor to review.

* **Document ID:** (Auto-generated)
* **Fields:**
    * `customer_id` (string): A unique ID for the customer in the call.
        * *Example: "customer_123"*
    * `question_text` (string): The exact question the customer asked.
        * *Example: "Do you offer student discounts?"*
    * `received_at` (timestamp): When the agent created this help request.
    * `resolved_at` (timestamp): (Optional) When the supervisor resolved the request.
    * `status` (string): The current state of the request.
        * *Example: "Resolved", "Pending"*
    * `supervisor_response` (string): (Optional) The answer provided by the supervisor.
        * *Example: "Yes"*

## Key Data Flows

Explain the step-by-step process for a primary feature.

**Example: A New Call**
1.  A customer connects to the `agent`, the Python `agent` is also in the room, listening.
2.  The agent greets the customer and tells what query does he/she needs help with.
3.  As the user speaks, the `agent` transcribes, checks the database, and acts accordingly.
4.  If the `agent` knows the answer, it says the answer to the customer if not, it raises a request to its supervisor which can be seen in the `supervisor-ui`.
5.  The `supervisor-ui` listens for real-time updates from the `agent`, if it gets a query it resolves as per the requirement.
6.  If the supervisor is not available, the query gets stored in the database and the request gets timed out after 3 minutes, which can be resolved later.

***

## Design Decisions

* **Why a Monorepo?**
    A monorepo was used for **organizational simplicity**. It allows all three core components of this single application (`supervisor-ui`, `functions`, and `agent`) to be managed in one repository. This makes the project easier to clone, understand, and manage as a single, cohesive unit.

* **Why LiveKit?**
    The project is built on the **LiveKit agent framework**. This was a key technical decision as it provides the entire scaffolding for a conversational AI agent. It abstracts the complex plumbing of real-time audio and, most importantly, provides built-in integrations for various AI models. This allowed the project to easily plug in best-in-class services for each task:
    * **LLM:** `openai/gpt-4o-mini`
    * **STT (Speech-to-Text):** `assemblyai/universal-streaming:en`
    * **TTS (Text-to-Speech):** `cartesia/sonic-2`

* **Why Firebase?**
    Firebase was chosen as the **Backend-as-a-Service (BaaS)** for its serverless nature and powerful, integrated features:
    * **Firestore:** A NoSQL database whose **real-time update** (snapshot listener) feature is the most critical part of the `supervisor-ui`. It allows new `help_requests` to appear on the admin's screen instantly without them needing to refresh.
    * **Firebase Functions:** Provides a serverless backend for any business logic (like generating LiveKit tokens), removing the need to build and manage a separate server.
    * **Firebase Emulator Suite:** Allows the entire backend (database and functions) to be run and tested 100% locally, which drastically speeds up development and debugging.

* **Why Next.js?**
    Next.js was chosen to build the `supervisor-ui`. Instead of a basic React application, Next.js provides a robust, production-ready framework out of the box. This includes a file-based routing system, optimized performance, and a superior developer experience (like fast refresh) that makes building the admin panel more efficient.