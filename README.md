# FloraCare - Plant Care & Greenhouse Assistant

> An intelligent, conversational greenhouse assistant powered by Google Agent Development Kit (ADK), Gemini 2.5 Flash, Vertex AI Memory Bank, Cloud Firestore, and Cloud Storage.

<div align="center">

![FloraCare Demo](demo.gif)

</div>

FloraCare helps plant enthusiasts care for their houseplants, track watering schedules, look up botanical care profiles, check real-time weather advisories, discover local garden nurseries, and generate plant care videos.

---

## 🌟 Key Capabilities & Implemented Tools

All capabilities listed below are actively implemented and wired into the agent (`app/agent.py` and `agents-cli-manifest.yaml`):

### 🧠 Cross-Session Long-Term Memory (Vertex AI Memory Bank)
* **Preload Memory Tool (`PreloadMemoryTool`)**: Recalls user facts, houseplant collection details, pot materials (e.g., terracotta vs. ceramic/plastic), ambient room lighting conditions, and experience level across separate chat sessions.
* **Turn Memory Callback (`generate_memories_callback`)**: Automatically extracts and writes conversation turn events into Vertex AI Memory Bank (`VertexAiMemoryBankService`) after each interaction so advice personalizes over time.

### 🗄️ Plant Catalog & Care Logging (Cloud Firestore)
* **`list_plants`**: Lists all available plants in the catalog with care difficulty, light requirements, watering frequency, pricing, and stock count.
* **`get_plant`**: Retrieves a detailed botanical profile for a specific species by name.
* **`search_plants_by_care`**: Filters the catalog by care difficulty (`Easy`, `Medium`, `Difficult`), lighting requirements (`Low`, `Medium`, `Bright`), and infrequent watering tolerance.
* **`add_plant_to_catalog`**: Adds new plant records to the Firestore catalog collection.
* **`log_plant_care_event`**: Persists timestamped maintenance actions (watering, fertilizing, pruning, repotting) to the `care_logs` Firestore collection.

### 💧 Dynamic Watering Schedule Calculation
* **`calculate_watering_schedule`**: Computes precision watering intervals based on:
  * Plant species baseline requirements
  * Pot material evaporation curves (e.g., porous terracotta dries out ~15-20% faster than glazed plastic)
  * Ambient light intensity (low, medium, bright indirect)
  * Days elapsed since last watering
* Returns days until next watering, status warnings (`Water Now`, `Water Soon`, `OK`), and physical soil finger-test guidance.

### 🌤️ Live Weather & Microclimate Advisories (Open-Meteo API)
* **`get_live_weather` / `get_weather`**: Fetches real-time temperature, humidity, and forecast conditions for any city.
* Generates actionable plant advisories (e.g., dry indoor air warnings when humidity drops below 40%, frost alerts, and seasonal transpiration adjustments).

### 📍 Local Nursery & Florist Discovery (Google Maps APIs)
* **`geocode_address`**: Converts street addresses or city names into geographic coordinates.
* **`find_nearby_places`**: Locates nearby plant nurseries, florists, botanical gardens, and garden supply centers.

### 🎥 AI Video Generation (Google Omni & Cloud Storage)
* **`generate_plant_video`**: Generates short plant videos using Google's Omni model (`gemini-omni-flash-preview` in the global region).
* Saves the video artifact in the agent context (`tool_context.save_artifact`) and streams the raw video bytes directly into a public Google Cloud Storage bucket (`floracare-media-...`), returning the public HTTPS URL without writing local temporary files.

### 🧪 Secure Python Code Execution Sandbox
* **`AgentEngineSandboxCodeExecutor`**: Safely executes Python code in an isolated Agent Engine sandbox environment to perform exact mathematical calculations (e.g., fertilizer dilution ratios, pot soil volume formulas, and container dimensions).

---

## 📋 Status of Planned Features

To maintain transparency between the initial project brief and current implementation:

| Feature | Status | Notes |
|---|---|---|
| **Watering Schedule Calculator** | ✅ Implemented | Full algorithmic calculation factoring pot material & light |
| **Cross-Session Memory** | ✅ Implemented | Backed by Vertex AI Memory Bank |
| **Firestore Database Catalog** | ✅ Implemented | Live CRUD queries for plants and care logs |
| **Cloud Storage Video Generation** | ✅ Implemented | Powered by `gemini-omni-flash-preview` & GCS bucket |
| **Weather & Microclimate Advisories** | ✅ Implemented | Live Open-Meteo weather integration |
| **Google Maps Place Discovery** | ✅ Implemented | Geocoding and nearby nursery discovery |
| **Agent Engine Python Sandbox** | ✅ Implemented | Runs custom Python code in cloud sandbox |
| **Botanical Chat Frontend** | ✅ Implemented | FastAPI web app with prompt chips, dialogue layout, video player |
| **Image Generation (`gemini-3.1-flash-lite-image`)** | ⏳ Planned | Planned, not yet implemented (video generation implemented instead) |
| **A2UI Rich Component Cards** | ⏳ Planned | Planned, not yet implemented (frontend currently renders markdown) |

---

## 🏗️ Project Architecture

```
BuildWithGemini/
├── floracare/                 # Core Agent Package
│   ├── app/
│   │   ├── agent.py          # Root agent definition, instructions, and tool registry
│   │   ├── db.py             # Firestore catalog and care log queries
│   │   ├── watering.py       # Watering schedule math & pot material adjustments
│   │   ├── weather.py        # Open-Meteo live weather & plant advisory
│   │   ├── maps.py           # Geocoding & nursery places discovery
│   │   ├── video.py          # Omni video generation & Cloud Storage upload
│   │   ├── fast_api_app.py   # ADK FastAPI service adapter
│   │   └── app_utils/        # A2A and reasoning engine adapters
│   ├── pyproject.toml        # Agent Python dependencies
│   └── agents-cli-manifest.yaml # Agent Engine manifest
│
├── frontend/                 # Shareable Web Frontend
│   ├── main.py               # FastAPI proxy forwarding requests to the agent
│   ├── requirements.txt      # Frontend dependencies
│   └── static/
│       └── index.html        # Botanical UI with prompt chips, bubbles, and video support
│
├── demo.gif                  # Screen-capture demo of FloraCare
└── project_brief.md          # Original project brief & design specs
```

---

## 🚀 Local Setup & Run Instructions

### Prerequisites
* **Python 3.11+**
* [**uv**](https://docs.astral.sh/uv/) (fast Python package and project manager)
* [**agents-cli**](https://google.github.io/agents-cli/) (`uv tool install google-agents-cli`)
* [**Google Cloud SDK**](https://cloud.google.com/sdk/docs/install) (`gcloud`)

### 1. Authenticate with Google Cloud
Ensure your local environment has authenticated Google Cloud credentials:
```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project <YOUR_GCP_PROJECT_ID>
```

### 2. Run the Agent Locally (ADK Playground)
Navigate into the agent folder and launch the ADK development environment:
```bash
cd floracare

# Install dependencies
agents-cli install

# Start the interactive agent playground
agents-cli playground
```
This starts the local ADK server where you can interact directly with the agent, inspect tool calls, and observe memory events.

### 3. Run the Custom Web Frontend
In a separate terminal, launch the FastAPI web frontend proxy:
```bash
cd frontend

# Install frontend dependencies
uv pip install -r requirements.txt

# Run the frontend application
python main.py
```
By default, the frontend server binds to port 8080 and provides the themed chat interface with quick-prompt chips.

---

## 🧪 Testing & Evaluation

Run unit and integration test suites:
```bash
cd floracare
uv run pytest tests/
```

Run agent evaluation benchmarks with `agents-cli`:
```bash
cd floracare
agents-cli eval
```

---

## 📄 License

This project is licensed under the Apache License 2.0.
