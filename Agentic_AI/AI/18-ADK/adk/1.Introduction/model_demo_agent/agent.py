from google.adk.agents import SequentialAgent,LlmAgent,ParallelAgent,LoopAgent,BaseAgent
from google.adk.models.lite_llm import LiteLlm

open_router_model = LiteLlm(model='openrouter/deepseek/deepseek-chat-v3-0324:free'
                            ,api_key='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')

root_agent = LlmAgent(
    model=open_router_model,
    name='root_agent',
    description='A helpful assistant for user questions.',
    instruction='Answer user questions to the best of your knowledge',
)
