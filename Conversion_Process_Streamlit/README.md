# Code Documentation and Test Generator - Streamlit App

This is a Streamlit version of the Code Documentation and Test Generator workflow. It provides a user-friendly interface for adding documentation to code and generating tests with human-in-the-loop review.

## Features

- Add documentation to Python code using AI
- Human review of the generated documentation
- Generate test cases for the documented code
- Support for multiple LLM providers (Azure OpenAI, OpenAI, Anthropic, Groq, Gemini)
- Persistent workflow state

## Setup

1. Clone the repository
2. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your LLM API keys (see `.env.example`)
4. Run the Streamlit app:
   ```
   streamlit run streamlit_app.py
   ```

## Environment Variables

Create a `.env` file with the following variables:

```
# LLM Provider (azure_openai, openai, anthropic, groq, gemini)
LLM_PROVIDER=azure_openai

# Azure OpenAI
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_DEPLOYMENT_NAME=your_deployment_name
AZURE_OAI_MODEL=gpt-4o
AZURE_OPENAI_API_VERSION=2023-05-15

# OpenAI
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key
ANTHROPIC_MODEL=claude-3-opus-20240229

# Groq
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama3-70b-8192

# Gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-pro
```

## Workflow

1. Enter your Python code in the input field
2. The AI adds documentation to your code
3. Review the documentation and provide feedback
4. If approved, the AI generates test cases for your code
5. If rejected, the AI improves the documentation based on your feedback

## License

This project is licensed under the MIT License - see the LICENSE file for details.
