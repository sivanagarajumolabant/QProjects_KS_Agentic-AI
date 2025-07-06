from google.adk.agents import Agent
import os
import dotenv
from google.adk.tools.crewai_tool import CrewaiTool
from crewai_tools import SerperDevTool
from google.adk.tools.agent_tool import AgentTool
dotenv.load_dotenv()


from google.adk.agents import Agent
from google.adk.tools import google_search
from zoneinfo import ZoneInfo
import datetime


SERPER_API_KEY = os.getenv('SERPER_API_KEY')
if not SERPER_API_KEY:
    raise ValueError("SERPER_API_KEY environment variable is not set.")



google_search_agent = Agent(
    model='gemini-2.0-flash-001',
    name='google_search_agent',
    # tools=[google_search],
    tools=[google_search], #Using a custom tool and a in-built tool together. This is not allowed in the current version.
    description='A helpful assistant for user questions.',
    instruction='''You are a helpful assistant. Answer the user\'s questions to the best of your ability using the provided tools.
        When you are asked for some information, you can use the google_search tool to search on the web.
    '''
)


serper_crewai_tool = SerperDevTool(
    country="in",
    locale="in",
    location="Mumbai, Maharashtra, India",
    n_results=10,
)

def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city.

    Args:
        city (str): The name of the city for which to retrieve the current time.

    Returns:
        dict: status and result or error msg.
    """

    if city.lower() == "new york":
        tz_identifier = "America/New_York"
    else:
        return  {
            "status": "error",
            "error_message": (
                f"Sorry, I don't have timezone information for {city}."
            ),
        }

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    report = (
        f'The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
    )
    return {"status": "success", "report": report}


adk_serper_tool = CrewaiTool(
    name = 'InternetNewsSearch',
    description= 'Search the internet for news articles and information using Serper',
    tool = serper_crewai_tool,
)

root_agent = Agent(
    model='gemini-2.0-flash-001',
    name='root_agent',
    description='A helpful assistant for user questions.',
    tools = [get_current_time,AgentTool(google_search_agent),adk_serper_tool],
    instruction='You are a helpful assistant. Answer user questions and use the tools to search web use google_search_agent AgentTool provided when necessary.',
)
