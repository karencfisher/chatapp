from langchain_community.tools import DuckDuckGoSearchResults

tools = [
    {
        "func": DuckDuckGoSearchResults().run,
        "name": "search",
        "description": "search the web for any current information to suppliment your previous training"
    }
]