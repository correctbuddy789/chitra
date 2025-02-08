import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI
import time
from typing import Optional, List, Dict
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

# --- Configuration ---
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

TMDB_API_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
PLACEHOLDER_IMAGE_URL = "https://via.placeholder.com/500x750?text=Poster+Not+Available"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# --- Helper Functions ---

def create_requests_session() -> requests.Session:
    """Creates a requests session with retry logic."""
    session = requests.Session()
    retries = Retry(total=MAX_RETRIES, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

def fetch_tmdb_data(movie_title: str) -> Optional[Dict]:
    """Fetches movie details (poster URL and year) from TMDB."""
    if not TMDB_API_KEY:
        return None

    session = create_requests_session()
    try:
        url = f"{TMDB_API_BASE_URL}/search/movie?api_key={TMDB_API_KEY}&query={movie_title}"
        response = session.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data['results']:
            movie = data['results'][0]
            poster_path = movie.get('poster_path')
            year = movie.get('release_date', '').split('-')[0]
            return {
                "poster_url": f"{TMDB_IMAGE_BASE_URL}{poster_path}" if poster_path else PLACEHOLDER_IMAGE_URL,
                "year": year if year else "N/A",
            }
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"TMDB API Error: {e}")
        return None

def generate_recommendations(liked_movie: str, liked_aspect: str, num_recommendations: int) -> Optional[List[Dict]]:
    """Generates movie recommendations using the DeepSeek API."""
    if not DEEPSEEK_API_KEY:
        st.error("DeepSeek API key not found. Please check your .env file.")
        return None

    # Update the base_url as per the API documentation
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

    messages = [
        {
            "role": "system", 
            "content": "You are a movie recommendation expert. Provide recommendations in valid JSON format."
        },
        {
            "role": "user",
            "content": (
                f"Based on the movie '{liked_movie}' that the user liked because '{liked_aspect}', "
                f"recommend {num_recommendations} movies, ranked by relevance. Format as JSON with this structure:\n\n"
                '{\n'
                '    "recommendations": [\n'
                '        {\n'
                '            "title": "Movie Title",\n'
                '            "description": "2-3 sentence description",\n'
                '            "reasoning": "Why you\'d like it based on '
                f"'{liked_aspect}' in '{liked_movie}'\"\n"
                '        }\n'
                '    ]\n'
                '}'
            )
        }
    ]

    for attempt in range(MAX_RETRIES):
        try:
            with st.spinner(f"Attempt {attempt + 1}/{MAX_RETRIES}: Getting recommendations..."):
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages,
                    stream=False,
                    max_tokens=1000,
                    temperature=0.7
                )
                content = response.choices[0].message.content
                st.write("Raw API response:", content)  # Debug: output raw response

                if not content.strip():
                    st.error("Empty response received from DeepSeek API.")
                    return None

                # Attempt to parse the JSON response
                recommendations = json.loads(content).get('recommendations')
                if recommendations is None:
                    st.error("JSON response does not contain 'recommendations'.")
                    st.code(content, language='json')
                    return None
                return recommendations

        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                st.warning(f"Request failed (attempt {attempt + 1}): {e}. Retrying in {RETRY_DELAY * (2 ** attempt)} seconds...")
                time.sleep(RETRY_DELAY * (2 ** attempt))
            else:
                st.error(f"Failed to get recommendations after multiple retries: {e}")
                if 'response' in locals() and hasattr(response, 'text'):
                    st.code(response.text, language='text')
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
                            st.image(PLACEHOLDER_IMAGE_URL, width=150)
                    with col2:
                        title = f"{i+1}. {rec['title']}"
                        year = f" ({tmdb_data['year']})" if tmdb_data else ""
                        st.markdown(f"### {title}{year}")
                        st.write(rec['description'])
                        st.markdown("**Why you'll like it:**")
                        st.write(rec['reasoning'])
                st.divider()
        else:
            st.error("Could not retrieve recommendations. Please try again later.")

st.markdown("---")
st.markdown("Built with ❤️ by [Tushar](https://www.linkedin.com/in/tusharnain/) - Mesa School of Business")
