import httpx
import json
import asyncio
from typing import TypedDict


class ModelArchitecture(TypedDict):
    modality: str
    input_modalities: list[str]
    output_modalities: list[str]
    tokenizer: str
    instruct_type: str | None


class ModelPricing(TypedDict):
    prompt: str
    completion: str
    request: str
    image: str
    web_search: str
    internal_reasoning: str


class ModelProvider(TypedDict):
    context_length: int
    max_completion_tokens: int | None
    is_moderated: bool


class Model(TypedDict):
    id: str
    name: str
    created: int
    description: str
    context_length: int
    architecture: ModelArchitecture
    pricing: ModelPricing
    top_provider: ModelProvider
    per_request_limits: dict | None


async def fetch_openrouter_models() -> list[Model]:
    """Fetches model information from OpenRouter API."""
    async with httpx.AsyncClient() as client:
        response = await client.get("https://openrouter.ai/api/v1/models")
        response.raise_for_status()
        data = response.json()

        models_data: list[Model] = []
        for model in data.get("data", []):
            # Skip models with '(free)' in the name or id = 'openrouter/auto'
            if (
                "(free)" in model.get("name", "")
                or model.get("id") == "openrouter/auto"
            ):
                continue

            models_data.append(model)

        return models_data


async def main() -> None:
    models = await fetch_openrouter_models()

    # Print the first model data in a nicely indented JSON format
    print(json.dumps(models[0], indent=4))

    with open("or-models.json", "w") as f:
        json.dump({"models": models}, f, indent=4)


if __name__ == "__main__":
    asyncio.run(main())
