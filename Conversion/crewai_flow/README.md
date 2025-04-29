# CrewAI Flow Code Processing Implementation

This implementation uses CrewAI Flow to process code through a pipeline of documentation, review, and test generation while maintaining state throughout the process.

## Features

- **Multi-Model Support**: Works with Azure OpenAI, OpenAI, Anthropic, Groq, and Gemini using CrewAI's LLM class
- **CrewAI Flow Implementation**: Uses CrewAI's Flow pattern with `@start`, `@listen`, and `@router` decorators
- **CrewAI Crew Integration**: Implements the Crew, Agents, and Tasks pattern within the Flow structure
- **State Management**: Maintains state throughout the flow execution
- **Flexible Configuration**: All model settings can be configured via environment variables or directly in code

## Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Set up your environment variables in a `.env` file:

```
# Choose your LLM provider
LLM_PROVIDER=openai  # Options: azure_openai, openai, anthropic, groq, gemini

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=4096

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_DEPLOYMENT_NAME=your_deployment_name
AZURE_OAI_MODEL=gpt-4o
AZURE_OPENAI_API_VERSION=2023-05-15
AZURE_OPENAI_TEMPERATURE=0.7
AZURE_OPENAI_MAX_TOKENS=4096

# Anthropic Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key
ANTHROPIC_MODEL=claude-3-opus-20240229
ANTHROPIC_TEMPERATURE=0.7
ANTHROPIC_MAX_TOKENS=4096

# Groq Configuration
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama3-70b-8192
GROQ_TEMPERATURE=0.7
GROQ_MAX_TOKENS=4096

# Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-pro
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=4096

# Set the LLM provider to use
LLM_PROVIDER=openai  # Options: azure_openai, openai, anthropic, groq, gemini
```

## Usage

Run the code processing workflow:

```bash
python main.py
```

## How It Works

The implementation combines the CrewAI Flow pattern with the Crew, Agents, and Tasks approach:

1. **Flow Structure**: The main flow is implemented using CrewAI's Flow pattern with multiple nodes:
   - `process_input_code`: Starting point that processes the input code
   - `add_documentation`: Adds documentation to the code using the crew
   - `review_documentation`: Reviews the documentation quality using the crew
   - `route_based_on_review`: Routes the flow based on the review result
   - `improve_documentation`: Improves documentation if needed using the crew
   - `generate_tests`: Generates test cases using the crew

2. **Crew Implementation**: The code processing tasks are handled by a CrewAI Crew:
   - Located in `crews/code_processing_crew/code_processing_crew.py`
   - Configured using Python files in `crews/code_processing_crew/config/`
   - Follows the CrewBase pattern with @agent, @task, and @crew decorators

3. **Agents**: Three specialized agents handle different aspects of code processing:
   - Code Documentation Specialist
   - Code Documentation Reviewer
   - Test Automation Specialist

4. **Tasks**: Four tasks define the work to be done:
   - `add_documentation_task`: Adds documentation to the code
   - `review_documentation_task`: Reviews documentation quality
   - `improve_documentation_task`: Improves documentation if needed
   - `generate_tests_task`: Generates test cases

5. **Pydantic Models**: Uses Pydantic models for structured data validation:
   ```python
   # Input models for tasks
   class AddDocumentationInput(BaseModel):
       input_code: str = Field(description="Original input code to be processed")

   # Result model for the workflow
   class CodeProcessingResult(BaseModel):
       input_code: str
       documented_code: str
       review_result: str
       test_code: Optional[str] = None
   ```

6. **Integration**: Each flow node creates a specialized crew for its task and calls the `kickoff` method with Pydantic models:
   ```python
   crew = Crew(
       agents=[self.code_processing_crew.code_documentation_reviewer()],
       tasks=[self.code_processing_crew.review_documentation_task()],
       process=Process.sequential,
       verbose=True
   )
   task_input = ReviewDocumentationInput(documented_code=documented_code)
   result = crew.kickoff(inputs=task_input.model_dump())
   ```

7. **State Management**: The workflow maintains state throughout the process using the `WorkflowState` model, tracking the code at each stage

8. **Flow Visualization**: The implementation includes a visualization feature to help understand the flow structure

## Customization

You can customize the implementation by:

1. Modifying agent configurations in `crews/code_processing_crew/config/agents_config.py`
2. Adjusting task descriptions in `crews/code_processing_crew/config/tasks_config.py`
3. Modifying the crew implementation in `crews/code_processing_crew/code_processing_crew.py`
4. Changing the flow structure in `workflow/workflow.py`
5. Changing the LLM provider in the `.env` file or directly in code

## Troubleshooting

If you encounter issues:

1. Check that your API keys are correct in the `.env` file
2. Ensure you have the correct dependencies installed
3. Verify that the LLM provider you've selected is properly configured
4. Check the console output for specific error messages

### LiteLLM Configuration

CrewAI uses LiteLLM under the hood, which has specific requirements for model names and configuration parameters.

#### Model Format

Model names should follow this pattern:

- Azure OpenAI: `azure/<deployment_name>`
- OpenAI: `openai/<model_name>`
- Anthropic: `anthropic/<model_name>`
- Groq: `groq/<model_name>`
- Gemini: `gemini/<model_name>`

#### Azure OpenAI Configuration

For Azure OpenAI, the recommended approach is to set environment variables and initialize the LLM with minimal parameters:

```python
# Set environment variables
os.environ["AZURE_API_KEY"] = "your-api-key"
os.environ["AZURE_API_BASE"] = "https://your-endpoint.openai.azure.com/"
os.environ["AZURE_API_VERSION"] = "2023-08-01-preview"

# Initialize LLM
llm = LLM(model="azure/your-deployment-name", api_version="2023-08-01-preview")
```

This approach is more reliable than passing all parameters in the config dictionary.

For more information, see the [LiteLLM documentation](https://docs.litellm.ai/docs/providers).
