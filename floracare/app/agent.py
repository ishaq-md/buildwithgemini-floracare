# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.db import (
    list_plants,
    get_plant,
    search_plants_by_care,
    add_plant_to_catalog,
    log_plant_care_event,
)
from app.watering import calculate_watering_schedule
from app.weather import get_live_weather
from app.maps import geocode_address, find_nearby_places
from app.video import generate_plant_video

MODEL = "gemini-3.8-flash"
MEMORY_BANK_ID = "2715860790816014336"
PROJECT_ID = "qwiklabs-gcp-04-bccd001ca2e2"
LOCATION = "us-east1"


def _get_sandbox_code_executor() -> AgentEngineSandboxCodeExecutor:
    """Initializes AgentEngineSandboxCodeExecutor using deployment metadata."""
    metadata_path = Path(__file__).resolve().parent.parent / "deployment_metadata.json"
    engine_id = f"projects/936971078949/locations/{LOCATION}/reasoningEngines/{MEMORY_BANK_ID}"
    sandbox_name = f"projects/936971078949/locations/{LOCATION}/reasoningEngines/{MEMORY_BANK_ID}/sandboxEnvironments/5657268799884230656"

    if metadata_path.exists():
        try:
            with open(metadata_path) as f:
                meta = json.load(f)
                engine_id = meta.get("remote_agent_runtime_id", engine_id)
                sandbox_name = meta.get("sandbox_resource_name", sandbox_name)
        except Exception:
            pass

    return AgentEngineSandboxCodeExecutor(
        sandbox_resource_name=sandbox_name,
        agent_engine_resource_name=engine_id,
    )


# WRITE: after each turn, send the session to Memory Bank for extraction.
async def generate_memories_callback(callback_context: CallbackContext):
    """Asynchronously writes turn session events to Memory Bank."""
    try:
        if getattr(callback_context._invocation_context, "memory_service", None) is None:
            from app.app_utils import services
            callback_context._invocation_context.memory_service = services.get_memory_service()
        await callback_context.add_session_to_memory()
    except Exception as e:
        logger.warning(f"Could not add session to memory: {e}")
    return None


def memory_bank_service_builder() -> VertexAiMemoryBankService:
    """Configures VertexAiMemoryBankService for deployed Agent Runtime container."""
    return VertexAiMemoryBankService(
        project=PROJECT_ID,
        location=LOCATION,
        agent_engine_id=MEMORY_BANK_ID,
    )


def get_weather(query: str) -> str:
    """Fetches real live weather and temperature for a city or region using Open-Meteo API.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with live real-time weather information and plant advisory.
    """
    data = get_live_weather(query)
    if "error" in data:
        return data["error"]
    return (
        f"The weather in {data['location']} is currently {data['temperature_f']}°F, "
        f"{data['conditions']}, with {data['humidity_percent']}% humidity. "
        f"Today's high is {data['today_high_f']}°F, low is {data['today_low_f']}°F. "
        f"Plant advisory: {data['plant_advisory']}"
    )


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


INSTRUCTION = """You are FloraCare, an expert greenhouse and houseplant care assistant.
You help plant owners care for their houseplants, calculate schedules, and discover new varieties.
You remember the user's stated preferences, home lighting conditions, plant experience, and past care history from previous conversations, and use them to personalize your advice.
You have access to a live Firestore database, real-time weather APIs, Google Maps tools, and a secure Python sandbox code executor.

Use your tools and capabilities:
- Browse and list available plants in the catalog (list_plants).
- Look up specific care details, lighting requirements, and watering schedules (get_plant).
- Search or filter plants based on care difficulty or lighting preferences (search_plants_by_care).
- Calculate personalized watering schedules and next watering dates (calculate_watering_schedule).
- Fetch live real-time weather, temperature, humidity, and microclimate guidance for any city (get_live_weather, get_weather).
- Convert an address or city into geographical coordinates (geocode_address).
- Discover nearby places such as plant nurseries, florists, garden centers, or parks (find_nearby_places).
- Generate short instructional or timelapse videos of plants using Google's Omni model (generate_plant_video).
- Add new plants to the catalog (add_plant_to_catalog).
- Record care actions such as watering, fertilizing, or repotting (log_plant_care_event).
- For complex mathematical calculations, fertilizer ratios, soil volumes, algorithms (like FizzBuzz), or running Python code, you have access to a Python sandbox. Run Python code in your code executor to compute the exact answer.

Always use your tools and code executor to provide accurate, verified answers.
"""

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=INSTRUCTION,
    code_executor=_get_sandbox_code_executor(),
    tools=[
        PreloadMemoryTool(),
        list_plants,
        get_plant,
        search_plants_by_care,
        calculate_watering_schedule,
        get_live_weather,
        get_weather,
        geocode_address,
        find_nearby_places,
        generate_plant_video,
        add_plant_to_catalog,
        log_plant_care_event,
        get_current_time,
    ],
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
