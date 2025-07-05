import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.tools import FunctionTool
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Please set the OPENAI_API_KEY environment variable.")

# Initialize the OpenAI model client
openai_client = OpenAIChatCompletionClient(model="gpt-4o-mini", api_key=api_key)

# Define a custom function to reverse a string
def reverse_string(text: str,) -> str:
    """Reverse the given text."""
    return text[::-1]

async def fetch_webpage(
    url: str, include_images: bool = True, max_length: Optional[int] = None, headers: Optional[Dict[str, str]] = None
) -> str:
    """Fetch a webpage and convert it to markdown format.

    Args:
        url: The URL of the webpage to fetch
        include_images: Whether to include image references in the markdown
        max_length: Maximum length of the output markdown (if None, no limit)
        headers: Optional HTTP headers for the request

    Returns:
        str: Markdown version of the webpage content

    Raises:
        ValueError: If the URL is invalid or the page can't be fetched
    """
    # Use default headers if none provided
    if headers is None:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        # Fetch the webpage
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Convert relative URLs to absolute
            for tag in soup.find_all(["a", "img"]):
                if tag.get("href"):
                    tag["href"] = urljoin(url, tag["href"])
                if tag.get("src"):
                    tag["src"] = urljoin(url, tag["src"])

            # Configure HTML to Markdown converter
            h2t = html2text.HTML2Text()
            h2t.body_width = 0  # No line wrapping
            h2t.ignore_images = not include_images
            h2t.ignore_emphasis = False
            h2t.ignore_links = False
            h2t.ignore_tables = False

            # Convert to markdown
            markdown = h2t.handle(str(soup))

            # Trim if max_length is specified
            if max_length and len(markdown) > max_length:
                markdown = markdown[:max_length] + "\n...(truncated)"

            return markdown.strip()

    except httpx.RequestError as e:
        raise ValueError(f"Failed to fetch webpage: {str(e)}") from e
    except Exception as e:
        raise ValueError(f"Error processing webpage: {str(e)}") from e

# Register the custom function as a tool
reverse_tool = FunctionTool(reverse_string,description='A tool to reverse a string')

# Create an agent with the custom tool
agent = AssistantAgent(
    name="ReverseAgent",
    model_client=openai_client,
    system_message="You are a helpful assistant that can reverse text using the reverse_string tool.",
    tools=[reverse_tool],
    reflect_on_tool_use=True,
)

# Define a task
task = "Reverse the text 'Hello, how are you?'"

# Run the agent
async def main():
    result = await agent.run(task=task)
    
    print(f"Agent Response: {result.messages[-1].content}")

if __name__ == "__main__":
    asyncio.run(main())