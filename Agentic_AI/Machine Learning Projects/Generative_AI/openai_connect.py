import openai

openai.api_key = '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'

response = openai.Completion.create(
    engine='text-davinci-003',  # Specify the engine (GPT-3.5)
    prompt='Hello, how are you?',  # Provide a user message or conversation history
    max_tokens=50  # Set the maximum number of tokens for the response
)

resp = response['choices'][0]['text']
print(resp)
