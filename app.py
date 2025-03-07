import os
import requests
import hashlib
import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pinecone import Pinecone
from pinecone import ServerlessSpec
from search_tools import search_duckduckgo, search_youtube
import tkinter as tk
from tkinter import scrolledtext
import webbrowser

# Load environment variables
load_dotenv()

# Set API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("INDEX_NAME")

if not OPENAI_API_KEY or not OMDB_API_KEY or not PINECONE_API_KEY or not PINECONE_INDEX_NAME:
    raise ValueError("Please set all API keys and Pinecone index name in your .env file.")

# Initialize OpenAI model & embeddings
llm = ChatOpenAI(model="gpt-4", temperature=0, openai_api_key=OPENAI_API_KEY)
embed_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
if PINECONE_INDEX_NAME not in pc.list_indexes().names():
    print(f"Creating Pinecone index: {PINECONE_INDEX_NAME}...")
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
index = pc.Index(PINECONE_INDEX_NAME)

def get_embedding(text):
    return embed_model.embed_query(text)

def search_media(title, media_type="movie"):
    print(f"\n🔍 Searching for: {title} ({media_type})")  # Debugging
    
    query_embedding = get_embedding(title)
    query_result = index.query(vector=query_embedding, top_k=1, include_metadata=True)

    if query_result and query_result.matches:
        match = query_result.matches[0]
        if match.score > 0.85:
            print("✅ Retrieved from Pinecone cache.\n")
            return match.metadata
    
    url = f"http://www.omdbapi.com/?t={title}&type={media_type}&apikey={OMDB_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if data.get("Response") == "True":
            print("🎬 OMDB Data Retrieved Successfully!")

            # YouTube trailer search
            trailer_links = search_youtube(title)
            if isinstance(trailer_links, list):
                trailer_links = ", ".join([trailer["url"] for trailer in trailer_links if isinstance(trailer, dict) and "url" in trailer])

            # DuckDuckGo search
            ddg_results = search_duckduckgo(title + " movie")
            print(f"🔎 Raw DuckDuckGo Results: {ddg_results}")  # Debugging

            # Extract links correctly
            if isinstance(ddg_results, list) and all(isinstance(res, str) for res in ddg_results):
                ddg_links = [res.split(" - ")[-1] for res in ddg_results if " - " in res]
            else:
                ddg_links = ["No related links found."]

            print(f"🌐 Extracted Links: {ddg_links}")  # Debugging

            media_details = {
                "Title": data.get("Title"),
                "Year": data.get("Year"),
                "Director": data.get("Director", "N/A"),
                "Cast": data.get("Actors"),
                "IMDB Rating": data.get("imdbRating"),
                "Genre": data.get("Genre"),
                "Seasons": data.get("totalSeasons") if media_type == "series" else "N/A",
                "Plot": data.get("Plot"),
                "Trailer": trailer_links if trailer_links else "No trailers found.",
                "Related Links": ddg_links if ddg_links else ["No related links found."]
            }

            # Store in Pinecone
            doc_id = hashlib.sha256(title.encode()).hexdigest()
            index.upsert(vectors=[(doc_id, query_embedding, media_details)])
            print("\n✅ Stored in Pinecone for future retrieval.\n")

            return media_details
        else:
            return {"Error": "Media not found. Check the title and try again."}
    return {"Error": "Failed to retrieve data. Please try again later."}

# Function to open links
def open_link(event):
    widget = event.widget
    index = widget.index(tk.CURRENT)
    link = widget.get(index + " wordstart", index + " wordend")
    webbrowser.open(link)

def search_and_display():
    media_type = media_type_var.get()
    user_query = search_entry.get().strip()
    result = search_media(user_query, media_type)
    search_results.config(state=tk.NORMAL)
    search_results.delete(1.0, tk.END)
    search_results.insert(tk.END, f"Search Query: {user_query}\n\n")
    
    for key, value in result.items():
        if key == "Trailer" or key == "Related Links":
            search_results.insert(tk.END, f"{key}:\n")
            if isinstance(value, list):
                for link in value:
                    search_results.insert(tk.END, f"{link}\n", ("link",))
            else:
                search_results.insert(tk.END, f"{value}\n", ("link",))
        else:
            search_results.insert(tk.END, f"{key}: {value}\n")

    search_results.tag_config("link", foreground="blue", underline=True)
    search_results.tag_bind("link", "<Button-1>", open_link)
    search_results.config(state=tk.DISABLED)

# Tkinter GUI
app = tk.Tk()
app.title("Movie/Series Search")
app.geometry("600x400")

media_type_var = tk.StringVar(value="movie")
search_entry = tk.Entry(app, width=50)
search_entry.pack(pady=10)

movie_button = tk.Radiobutton(app, text="Movie", variable=media_type_var, value="movie")
series_button = tk.Radiobutton(app, text="Series", variable=media_type_var, value="series")
movie_button.pack()
series_button.pack()

search_button = tk.Button(app, text="Search", command=search_and_display)
search_button.pack(pady=10)

search_results = scrolledtext.ScrolledText(app, width=70, height=15, state=tk.DISABLED)
search_results.pack()

app.mainloop()
