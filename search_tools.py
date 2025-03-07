import time
from duckduckgo_search import DDGS
import yt_dlp
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import Tool

# Define Web Search Tool (DuckDuckGo)
search_tool = Tool(
    name="DuckDuckGo Search",
    func=DuckDuckGoSearchRun().run,
    description="Searches the web using DuckDuckGo for real-time information."
)

# Function to search the web using DuckDuckGo
def search_duckduckgo(query):
    time.sleep(2)  # Prevent rapid requests
    results = DDGS().text(query, max_results=3)
    
    if not results:
        return ["No relevant results found."]
    
    return [f"{r['title']} - {r['href']}" for r in results]

# Function to search YouTube for trailers
# Function to search YouTube for trailers
def search_youtube(query):
    ydl_opts = {
        "quiet": True,
        "default_search": "ytsearch5",  # Search YouTube for top 5 results
        "format": "best",
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        search_results = ydl.extract_info(f"{query} trailer", download=False)
        
        if "entries" in search_results and search_results["entries"]:
            return [
                {"title": vid["title"], "url": vid["webpage_url"]}
                for vid in search_results["entries"] if "webpage_url" in vid
            ]
        else:
            return [{"title": "No trailer found", "url": "https://www.youtube.com/results?search_query=" + query + "+trailer"}]

# Test the search functions
if __name__ == "__main__":
    print("DuckDuckGo Search:", search_duckduckgo("Inception IMDB rating"))
    print("YouTube Search:", search_youtube("Inception movie trailer"))
