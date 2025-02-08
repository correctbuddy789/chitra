import streamlit as st
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
TMDB_API_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
PLACEHOLDER_IMAGE_URL = "https://via.placeholder.com/500x750?text=Poster+Not+Available"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


# --- Helper Functions ---

def create_session():
    """Creates a requests session with retry logic."""
    session = requests.Session()
    retries = Retry(total=MAX_RETRIES, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

def fetch_tmdb_data(movie_title):
    """Fetches movie details (poster URL and year) from TMDB."""
    if not TMDB_API_KEY:
        return None  # Handle missing API key

    session = create_session()
    try:
        url = f"{TMDB_API_BASE_URL}/search/movie?api_key={TMDB_API_KEY}&query={movie_title}"
        response = session.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data['results']:
            movie = data['results'][0]
            poster_path = movie.get('poster_path')
            year = movie.get('release_date', '').split('-')[0]  # Extract year
            return {
                "poster_url": f"{TMDB_IMAGE_BASE_URL}{poster_path}" if poster_path else PLACEHOLDER_IMAGE_URL,
                "year": year if year else "N/A",
            }
        return None  # No results found
    except requests.exceptions.RequestException as e:
        print(f"TMDB API Error: {e}")  # Log the error
        return None

def generate_recommendations(liked_movie, liked_aspect, num_recommendations):
    """Generates movie recommendations using the DeepSeek API."""
    if not DEEPSEEK_API_KEY:
        return None  # Handle missing API key

    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "deepseek-reasoner",
        "messages": [
            {"role": "system", "content": "You are a movie recommendation expert. Provide recommendations in valid JSON format."},
            {"role": "user", "content": f"""Based on the movie '{liked_movie}' that the user liked because '{liked_aspect}',
recommend {num_recommendations} movies, ranked by relevance. Format as JSON with this structure:
{{
    "recommendations": [
        {{
            "title": "Movie Title",
            "description": "2-3 sentence description",
            "reasoning": "Why you'd like it based on '{liked_aspect}' in '{liked_movie}'"
        }}
    ]
}}"""}
        ],
    }

    session = create_session()
    for attempt in range(MAX_RETRIES):
        try:
            response = session.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=30)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            response_json = response.json()

            # Check for 'choices' and get the content.  More robust than assuming the structure.
            if 'choices' in response_json and response_json['choices']:
                content = response_json['choices'][0]['message']['content'].strip()

                # Robust JSON parsing with error handling:
                try:
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.endswith("```"):
                        content = content[:-3]
                    recommendations = json.loads(content)['recommendations']
                    return recommendations  # Successful parsing!
                except json.JSONDecodeError as e:
                    st.error(f"JSON Decode Error: {e}")
                    st.text("Raw API Response (for debugging):")
                    st.code(content, language='text')
                    return None # Return after the error message


            else:
                st.error("DeepSeek API returned an unexpected response format.")
                st.text("Raw API Response (for debugging):")
                st.code(response.text, language='text')  # Show the raw response
                return None


        except requests.exceptions.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                st.warning(f"Request failed (attempt {attempt + 1}): {e}. Retrying in {RETRY_DELAY * (2 ** attempt)} seconds...")
                time.sleep(RETRY_DELAY * (2 ** attempt))  # Exponential backoff
            else:
                st.error(f"Request failed after multiple retries: {e}")
                return None
    return None


# --- Streamlit App ---

st.title("🎬🌟 Chitra the Movie Recommender")

with st.form("movie_form"):
    liked_movie = st.text_input("Enter a movie you liked:")
    liked_aspect = st.text_input("What did you like about it?")
    num_recommendations = st.number_input("Number of recommendations:", min_value=1, max_value=5, value=3)
    submit_button = st.form_submit_button("Get Recommendations")

if submit_button:
    if not liked_movie or not liked_aspect:
        st.warning("Please enter both a movie and what you liked about it.")
    else:
        recommendations = generate_recommendations(liked_movie, liked_aspect, num_recommendations)

        if recommendations:
            st.success("Here are your personalized movie recommendations:")
            for i, rec in enumerate(recommendations):
                tmdb_data = fetch_tmdb_data(rec['title'])
                with st.container():
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if tmdb_data:
                            st.image(tmdb_data['poster_url'], width=150)
                        else:
                            st.image(PLACEHOLDER_IMAGE_URL, width=150) #Default show of image
                    with col2:
                        title = f"{i+1}. {rec['title']}"
                        year = f" ({tmdb_data['year']})" if tmdb_data else ""
                        st.markdown(f"### {title}{year}")
                        st.write(rec['description'])
                        st.markdown("**Why you'll like it:**")
                        st.write(rec['reasoning'])
                st.divider()
        elif recommendations is None: # Explicit check since empty list is falsy
            st.error("Could not retrieve recommendations. Please check your API keys or try again later.")

st.markdown("---")
st.markdown("Built with ❤️ by [Tushar](https://www.linkedin.com/in/tusharnain/) - Mesa School of Business")
