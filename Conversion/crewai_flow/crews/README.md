# CrewAI Crews Implementation

This folder contains the implementation of CrewAI Crews for the code processing workflow.

## Structure

- `code_processing_crew/`: Contains the implementation of the code processing crew
  - `config/`: Configuration files for agents and tasks
    - `agents_config.py`: Agent configurations
    - `tasks_config.py`: Task configurations
  - `code_processing_crew.py`: Main crew implementation
  - `__init__.py`: Package initialization

## How It Works

The code processing crew implementation follows the CrewAI Crew pattern:

1. **Agents**: Three specialized agents handle different aspects of code processing:
   - Code Documentation Specialist
   - Code Documentation Reviewer
   - Test Automation Specialist

2. **Tasks**: Four tasks define the work to be done:
   - `add_documentation_task`: Adds documentation to the code
   - `review_documentation_task`: Reviews documentation quality
   - `improve_documentation_task`: Improves documentation if needed
   - `generate_tests_task`: Generates test cases

3. **Crew**: The `CodeProcessingCrew` class orchestrates the agents and tasks

4. **Flow Integration**: The crew is integrated with the existing Flow implementation in `workflow/workflow.py`

## Usage

The crew is used by the `CodeProcessingFlow` class in the workflow module. The flow creates an instance of the crew and delegates the code processing to it.

```python
# Create the flow
flow = CodeProcessingFlow(llm.client)

# Set the input code
flow.state.input_code = "..."

# Execute the flow (this will use the crew implementation internally)
flow.kickoff()
```

## Customization

You can customize the implementation by:

1. Modifying agent configurations in `config/agents.yaml`
2. Adjusting task descriptions in `config/tasks.yaml`
3. Adding new tasks or agents to extend the workflow
