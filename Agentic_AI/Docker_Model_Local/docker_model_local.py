from openai import OpenAI


client = OpenAI(
    api_key="docker",
    base_url='http://localhost:12434/engines/v1'
)

result = client.chat.completions.create(
    model = 'ai/gemma3',
    messages = 
    [
        {"role": "system", "content": "please answer in a simple way"},
        {"role": "user", "content": "tell about apple phone"}
    ],
    # stream= True
)

print(result.choices[0].message.content)