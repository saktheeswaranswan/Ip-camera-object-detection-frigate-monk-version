"""OpenAI Provider for Frigate AI."""

import base64
from typing import Optional

from openai import OpenAI

from frigate.config import GenAIProviderEnum
from frigate.genai import GenAIClient, register_genai_provider


@register_genai_provider(GenAIProviderEnum.openai)
class OpenAIClient(GenAIClient):
    """Generative AI client for Frigate using OpenAI."""

    provider: OpenAI

    def _init_provider(self):
        """Initialize the client."""
        return OpenAI(api_key=self.genai_config.api_key)

    def _send(self, prompt: str, images: list[bytes]) -> Optional[str]:
        """Submit a request to OpenAI."""
        encoded_images = [base64.b64encode(image).decode("utf-8") for image in images]
        result = self.provider.chat.completions.create(
            model=self.genai_config.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image}",
                                "detail": "low",
                            },
                        }
                        for image in encoded_images
                    ]
                    + [prompt],
                },
            ],
        )
        if len(result.choices) > 0:
            return result.choices[0].message.content.strip()
        return None
