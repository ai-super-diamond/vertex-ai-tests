from anthropic import AnthropicVertex

LOCATION = "europe-west4"

client = AnthropicVertex(region=LOCATION, project_id="vertex-ai-project-skorec")

message = client.messages.create(
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "Send me a recipe for banana bread.",
        }
    ],
    model="claude-sonnet-4-5@20250929"
)
print(message.model_dump_json(indent=2))