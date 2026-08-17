import os
import sys
import threading
from google import genai

# Load GitHub PAT from environment variable
github_token = os.environ.get("REVIEWER_GITHUB_TOKEN")
if not github_token:
    print("Error: REVIEWER_GITHUB_TOKEN environment variable is not set.", file=sys.stderr)
    sys.exit(1)

# Load Google Project ID from environment variable
google_project_id = os.environ.get("GOOGLE_PROJECT_ID")
if not google_project_id:
    print("Error: GOOGLE_PROJECT_ID environment variable is not set.", file=sys.stderr)
    sys.exit(1)

repo = os.environ["GITHUB_REPOSITORY"]

# Read instructions from stdin alternatively
if not sys.stdin.isatty():
    instructions = sys.stdin.read().strip()
else:
    instructions = ""

if not instructions:
    print("Error: No instructions provided via stdin.", file=sys.stderr)
    sys.exit(1)

input_query = f"Perform a PR review in repo {repo} using Github token `{github_token}` by following the following instructions:\n\n {instructions}"

client = genai.Client(
    vertexai=True,
    project=google_project_id,
    location="global",
)

stream = client.interactions.create(
    agent="antigravity-preview-05-2026",
    agent_config={
        "type": "antigravity",
        "model": "gemini-3.6-flash",
    },
    input=input_query,
    environment={
        "type": "remote",
        "network": {
            "allowlist": [
                {"domain": "*"}
            ]
        },
        "sources": [
            {
                "type": "gcs",
                "source": f"gs://{google_project_id}-skills",
                "target": "./skills"
            }
        ],
    },
    stream=True,
    background=True,
    store=True,
)

timeout_seconds = float(os.environ.get("INTERACTION_TIMEOUT", "600"))
interaction_id = None


def cancel_interaction():
    print(f"Error: Interaction timed out after {timeout_seconds} seconds.", file=sys.stderr)
    if interaction_id:
        try:
            client.interactions.cancel(id=interaction_id)
        except Exception:
            pass
    sys.stderr.flush()
    sys.stdout.flush()
    os._exit(1)


timer = threading.Timer(timeout_seconds, cancel_interaction)
timer.start()

try:
    for event in stream:
        if not interaction_id:
            if hasattr(event, "interaction") and event.interaction and hasattr(event.interaction, "id"):
                interaction_id = event.interaction.id
            elif hasattr(event, "id") and getattr(event, "id"):
                interaction_id = event.id

        print(event)
finally:
    timer.cancel()

