# AI CallDesk Advisor - Setup Guide

Voice agent handling customer relationships end-to-end using LiveKit, Firebase, and Next.js

## Prerequisites

Before starting, ensure you have the following installed:

- **Node.js** (v18 or higher)
- **Python** (v3.9 or higher)
- **Java** (JDK 11.0 or higher)
- **pnpm** (Install globally: `npm install -g pnpm`)
- **Firebase CLI** (Install: `npm install -g firebase-tools`)
- **LiveKit CLI** (Install: `winget install LiveKit.LiveKitCLI`)
- **Git** (for cloning the repository)

### Required API Keys

You'll need API keys for the following services:

- LiveKit Cloud account (Cloud URL and API credentials)
- Firebase project credentials (If using Firebase cloud for setup, else can use firebase emulator locally)

## Project Structure

```
frontdesk-advisor/
├── agents/           # LiveKit voice agent (Python)
├── functions/        # Firebase Cloud Functions
├── supervisor-ui/    # Next.js admin panel
└── README.md
```

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/RitamPal26/frontdesk-advisor.git
cd frontdesk-advisor
```

### 2. Setup Agents (LiveKit Voice AI Agent)

Navigate to the agents folder:

```bash
cd agents
```

**Install Python dependencies:**

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup the LiveKit project:
lk cloud auth

# Create a project/use an existing one
lk token create \
  --api-key <PROJECT_KEY> --api-secret <PROJECT_SECRET> \
  --join --room test_room --identity test_user \
  --valid-for 24h

# Set environment variables
lk app env -w

# Download model files
uv run agent.py download-files
```

**Configure environment variables:**

Create a `.env` file in the `agents/` directory:

```bash
# LiveKit Configuration
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
NEXT_PUBLIC_LIVEKIT_URL=wss://your-project.livekit.cloud
```

**Run the agent on web browser:**

```bash
uv run livekit_integration.py dev
```

Based on the Firebase documentation, here are the necessary changes for your functions setup section:

### 3. Setup Functions (Firebase Emulator & Firestore)

Navigate to the functions folder:

```bash
cd ../functions
```

**Initialize Firebase (if not already done):**

```bash
firebase login

firebase init emulators
# Select: Firestore, Functions, Emulators
# Choose existing project or create new one

# The CLI will ask you a few questions:
"What language would you like to use?": Choose TypeScript.
"Do you want to use ESLint?": Yes (Y).
"Do you want to install dependencies with npm now?": Yes (Y). 
```

**Start Firebase emulators:**

```bash
# First time start
firebase emulators:start

# In another terminal
firebase emulators:export ./firebase-data

# Persist the data between sessions:
firebase emulators:start --import=./firebase-data --export-on-exit
```

The Firestore emulator will run on `http://localhost:8080` and the UI on `http://localhost:4000`.

### 4. Setup Supervisor UI (Next.js Admin Panel)

Navigate to the supervisor-ui folder:

```bash
cd ../supervisor-ui
```

**Install dependencies:**

```bash
pnpm install
```

**Configure environment variables:**

Create a `.env.local` file in the `supervisor-ui/` directory:

```bash
# Firebase Configuration
NEXT_PUBLIC_FIREBASE_API_KEY=your_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_project_id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
NEXT_PUBLIC_FIREBASE_APP_ID=your_app_id

# Connect to local Firebase emulator (development only)
NEXT_PUBLIC_USE_EMULATOR=true
```

**Run the development server:**

```bash
pnpm dev
```

The admin panel will be available at `http://localhost:3000`.

## Running the Complete Stack Locally

Open **three terminal windows** and run each service:

**Terminal 1 - LiveKit Agent:**
```bash
cd agents
source venv/bin/activate  # or venv\Scripts\activate on Windows
uv run livekit_integration.py dev
```

**Terminal 2 - Firebase Functions:**
```bash
cd functions
firebase emulators:export ./firebase-data
```

**Terminal 3 - Next.js UI:**
```bash
cd supervisor-ui
pnpm dev
```