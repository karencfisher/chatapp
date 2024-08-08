from langchain_community.tools import DuckDuckGoSearchRun

tools = [
    {
        "func": DuckDuckGoSearchRun().run,
        "name": "search",
        "description": "search the web for any current information to suppliment your previous training"
    }
]