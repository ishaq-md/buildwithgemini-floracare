"""Video generation tool for FloraCare using Google Omni model (gemini-omni-flash-preview)."""

import asyncio
import base64
import logging
import uuid
from google import genai
from google.genai import types
from google.cloud import storage
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

# Hardcoded project and bucket name as strings
PROJECT_ID = "qwiklabs-gcp-04-bccd001ca2e2"
GCS_BUCKET_NAME = "floracare-media-qwiklabs-gcp-04-bccd001ca2e2"
MODEL_ID = "gemini-omni-flash-preview"
LOCATION = "global"


def _generate_video_bytes(prompt: str) -> bytes:
    """Invokes Google Omni model to generate video bytes in the global region."""
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION,
    )
    interaction = client.interactions.create(
        model=MODEL_ID,
        input=prompt,
        response_format={"type": "video"},
    )
    output_video = getattr(interaction, "output_video", None)
    if not output_video:
        raise ValueError("Omni model interaction did not return an output_video.")

    raw_data = getattr(output_video, "data", None)
    if raw_data is None:
        raise ValueError(f"No video data found in output_video: {output_video}")

    if isinstance(raw_data, str):
        return base64.b64decode(raw_data)
    elif isinstance(raw_data, (bytes, bytearray)):
        return bytes(raw_data)
    else:
        raise ValueError(f"Unexpected video data format: {type(raw_data)}")


def _upload_to_gcs(video_bytes: bytes, filename: str) -> str:
    """Uploads video bytes to the public Cloud Storage bucket without writing to disk."""
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(video_bytes, content_type="video/mp4")
    return f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"


async def generate_plant_video(
    plant_name: str,
    scene_description: str = "timelapse growth unfurling vibrant green leaves in natural daylight",
    tool_context: ToolContext | None = None,
) -> str:
    """Generates a short video for a houseplant using Google's Omni model (gemini-omni-flash-preview) in the global region.

    Saves the video to session artifacts and uploads it to the public Cloud Storage bucket.

    Args:
        plant_name: Name of the houseplant (e.g. 'Monstera Deliciosa', 'Fiddle Leaf Fig', 'Snake Plant').
        scene_description: Description of the action or scene to generate (e.g., 'watering plant with a watering can', 'timelapse growth of new leaf').
        tool_context: The ADK tool context used to record artifacts.

    Returns:
        The public HTTPS URL of the uploaded video (https://storage.googleapis.com/<bucket>/<object>).
    """
    prompt = f"Short high quality video of {plant_name}: {scene_description}. Smooth cinematic lighting, 720p."
    logger.info(f"Generating video with {MODEL_ID} (location={LOCATION}) for prompt: {prompt}")

    # Generate video in background thread to avoid blocking asyncio event loop
    video_bytes = await asyncio.to_thread(_generate_video_bytes, prompt)

    clean_name = "".join(c if c.isalnum() else "_" for c in plant_name.lower())[:20]
    filename = f"plant_{clean_name}_{uuid.uuid4().hex[:6]}.mp4"

    # 1. Save video artifact so it shows up in Playground's Artifacts panel
    if tool_context is not None:
        try:
            artifact_part = types.Part.from_bytes(data=video_bytes, mime_type="video/mp4")
            await tool_context.save_artifact(filename=filename, artifact=artifact_part)
            logger.info(f"Saved artifact {filename} to ToolContext.")
        except Exception as e:
            logger.warning(f"Could not save artifact to ToolContext: {e}")

    # 2. Upload video bytes to public Cloud Storage bucket (no local file written)
    public_url = await asyncio.to_thread(_upload_to_gcs, video_bytes, filename)
    logger.info(f"Uploaded video to Cloud Storage: {public_url}")

    return public_url
