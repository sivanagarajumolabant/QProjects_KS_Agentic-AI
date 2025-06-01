from autogen_core.models import UserMessage
from autogen_ext.models.ollama import OllamaChatCompletionClient
import asyncio

# ollama_model_client = OllamaChatCompletionClient(model='llama3.2')

# async def main():
#     response = await ollama_model_client.create([UserMessage(content='Hello, how are you?',source='user')])
#     print(response)
#     await ollama_model_client.close()

# asyncio.run(main())

from autogen_core.models import UserMessage
from autogen_ext.models.ollama import OllamaChatCompletionClient

# Assuming your Ollama server is running locally on port 11434.
ollama_model_client = OllamaChatCompletionClient(model="llama3.2")

async def main():
	response = await ollama_model_client.create([UserMessage(content="What is the capital of France?", source="user")])
	print(response)
	await ollama_model_client.close()

import asyncio
asyncio.run(main())
