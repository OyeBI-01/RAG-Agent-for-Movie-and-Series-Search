import os
import pinecone
from langchain.vectorstores import Pinecone as PineconeStore
from langchain.embeddings.openai import OpenAIEmbeddings  # Can be replaced with another embedding model
from langchain.schema import Document
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Pinecone API setup
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")  

# Initialize Pinecone
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
INDEX_NAME = "blessing"

# Ensure the index exists
if INDEX_NAME not in pinecone.list_indexes():
    pinecone.create_index(INDEX_NAME, dimension=1024, metric="cosine")  

# Connect to the Pinecone index
index = pinecone.Index(INDEX_NAME)


embed_model = OpenAIEmbeddings()

# Store the vector database
vector_store = PineconeStore(index, embed_model.embed_query)

def store_metadata(movie_data):
    """
    Store movie/TV show metadata in Pinecone.
    :param movie_data: Dict containing 'Title', 'Plot', etc.
    """
    doc = Document(
        page_content=movie_data["Plot"],
        metadata={
            "Title": movie_data["Title"],
            "Year": movie_data["Year"],
            "Director": movie_data.get("Director", "N/A"),
            "Cast": movie_data.get("Cast", "N/A"),
            "Genre": movie_data.get("Genre", "N/A"),
            "IMDB Rating": movie_data.get("IMDB Rating", "N/A"),
            "Trailer": movie_data.get("Trailer", "N/A")
        }
    )
    
    # Embed the document and store in Pinecone
    vector_store.add_documents([doc])
    print(f"Stored metadata for {movie_data['Title']} in Pinecone.")


def search_metadata(query):
    """
    Search for a movie/TV show based on a user query.
    :param query: Search query (e.g., "time travel sci-fi movies").
    :return: Best matching movie/TV show.
    """
    results = vector_store.similarity_search(query, k=3)  # Retrieve top 3 similar results
    return [result.metadata for result in results]


# Example usage
if __name__ == "__main__":
    test_movie = {
        "Title": "Interstellar",
        "Year": "2014",
        "Director": "Christopher Nolan",
        "Cast": "Matthew McConaughey, Anne Hathaway, Jessica Chastain",
        "IMDB Rating": "8.7",
        "Genre": "Adventure, Drama, Sci-Fi",
        "Plot": "When Earth becomes uninhabitable, an ex-NASA pilot leads a mission to find a new home for humanity.",
        "Trailer": "https://www.youtube.com/results?search_query=Interstellar+trailer"
    }
    
    store_metadata(test_movie)
    search_results = search_metadata("sci-fi movie about space exploration")
    print("Search Results:", search_results)
