from typing import Any
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.tools.wikidata.tool import WikidataAPIWrapper, WikidataQueryRun
from langchain_core.documents import Document
from langchain_community.utilities import WikipediaAPIWrapper


class WikpediaSearch(WikipediaAPIWrapper):
    """ Add Links to basic search output """
    @staticmethod
    def _formatted_page_summary(page_title: str, wiki_page: Any) -> str | None:
        output = WikipediaAPIWrapper._formatted_page_summary(page_title, wiki_page)
        return f"{output}\nSource: {wiki_page.url}"


class WikidataAPIWrapperFixed(WikidataAPIWrapper):
    """ Fixes bug in WikidataAPIWrapper"""
    def _item_to_document(self, qid):
        from wikibase_rest_api_client.utilities.fluent import FluentWikibaseClient

        fluent_client: FluentWikibaseClient = FluentWikibaseClient(
            self.wikidata_rest, supported_props=self.wikidata_props, lang=self.lang
        )
        resp = fluent_client.get_item(qid)

        if not resp:
            print(f"Could not find item {qid} in Wikidata")
            return None

        doc_lines = []
        if resp.label:
            doc_lines.append(f"Label: {resp.label}")
        if resp.description:
            doc_lines.append(f"Description: {resp.description}")
        if resp.aliases:
            doc_lines.append(f"Aliases: {', '.join(resp.aliases)}")
        for prop, values in resp.statements.items():
            if values:
                #doc_lines.append(f"{prop.label}: {', '.join(values)}")
                doc_lines.append(f"{prop.label}: {', '.join(map(str, values))}")

        return Document(
            page_content=("\n".join(doc_lines))[: self.doc_content_chars_max],
            meta={"title": qid, "source": f"https://www.wikidata.org/wiki/{qid}"},
        )
    

tools = [
    {
        "func": DuckDuckGoSearchResults().run,
        "name": "search",
        "description": "Search the web for any current information or to suppliment your previous \
                        training. Input should be a search query. Output is a JSON array of the \
                        query results."
    },

    {
        "func": WikidataQueryRun(api_wrapper=WikidataAPIWrapperFixed()).run,
        "name": "wikidata search",
        "description": "Wikidata search. \
                        Useful for when you need to answer general questions or get information about \
                        people, places, companies, facts, historical events, or other subjects. \
                        Returns an array of key/value pairs about the query subject. \
                        Input should be the exact name of the item you want information about."
    },

    {
        "func": WikpediaSearch().run,
        "name": "wikipedia search",
        "description": "Wikipedia search \
                        Useful for general topics such as science, mathetmatics, philosophy, history \
                        etc. Returns array of JSON results including summaries and links. Input should \
                        be a search query."
    }
]