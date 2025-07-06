from google.adk.agents import Agent
from google.adk.tools import google_search
from zoneinfo import ZoneInfo
import datetime


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



root_agent = Agent(
    model='gemini-2.0-flash-001',
    name='root_agent',
    # tools=[google_search],
    tools=[google_search,get_current_time], #Using a custom tool and a in-built tool together. This is not allowed in the current version.
    description='A helpful assistant for user questions.',
    instruction='''You are a helpful assistant. Answer the user\'s questions to the best of your ability using the provided tools.
        When you are asked for some information, you can use the google_search tool to search on the web.
    '''
)

