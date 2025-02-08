import streamlit as st
import os
from dotenv import load_dotenv
import time
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional, List, Dict
from openai import OpenAI

# --- Load Environment Variables ---
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# --- API Configuration ---
TMDB_API_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
PLACEHOLDER_IMAGE_URL = "https://via.placeholder.com/500x750?text=Poster+Not+Available"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# --- Helper Functions ---

def create_requests_session() -> requests.Session:
    """Create a requests session with retry logic for TMDB API calls."""
    session = requests.Session()
    retries = Retry(
        total=MAX_RETRIES, 
        backoff_factor=1, 
        status_forcelist=[429, 500, 502, 503, 504]
    )
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

def fetch_tmdb_data(movie_title: str) -> Optional[Dict]:
    """Fetch movie poster URL and release year from TMDB for the given movie title."""
    if not TMDB_API_KEY:
        st.error("TMDB API key not configured.")
        return None

    session = create_requests_session()
    try:
        url = f"{TMDB_API_BASE_URL}/search/movie?api_key={TMDB_API_KEY}&query={movie_title}"
        response = session.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('results'):
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
    """Generate movie recommendations using the DeepSeek API."""
    if not DEEPSEEK_API_KEY:
        st.error("DeepSeek API key not found. Please check your .env file.")
        return None

    # Initialize DeepSeek client with the correct base_url
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

    # Build the message payload to instruct the assistant to output JSON only.
    messages = [
        {
            "role": "system", 
            "content": "You are a movie recommendation expert. Provide recommendations in valid JSON format."
        },
        {
            "role": "user",
            "content": (
                f"Based on the movie '{liked_movie}' that the user liked because '{liked_aspect}', "
                f"recommend {num_recommendations} movies, ranked by relevance. "
                "Return the output as JSON strictly following this format:\n\n"
                '{\n'
                '    "recommendations": [\n'
                '        {\n'
                '            "title": "Movie Title",\n'
                '            "description": "2-3 sentence description",\n'
                '            "reasoning": "Why you would like it based on the liked aspect"\n'
                '        }\n'
                '    ]\n'
                '}'
            )
        }
    ]

    # Attempt to get a response with retries
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
                # Extract the message content from the response
                content = response.choices[0].message.content
                st.write("Raw API response:", content)  # Debug output

                if not content.strip():
                    st.error("Empty response received from DeepSeek API.")
                    return None

                # Parse the JSON content
                parsed = json.loads(content)
                recommendations = parsed.get('recommendations')
                if not recommendations:
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

# --- Streamlit App Layout ---

st.title("🎬🌟 Chitra the Movie Recommender")

with st.form("movie_form"):
    liked_movie = st.text_input("Enter a movie you liked:")
    liked_aspect = st.text_input("What did you like about it?")
    num_recommendations = st.number_input("Number of recommendations:", min_value=1, max_value=5, value=3)
    submit_button = st.form_submit_button("Get Recommendations")

if submit_button:
    if not liked_movie or not liked_aspect:
        st.warning("Please enter both a movie title and what you liked about it.")
    else:
        recommendations = generate_recommendations(liked_movie, liked_aspect, num_recommendations)
        if recommendations:
            st.success("Here are your personalized movie recommendations:")
            for idx, rec in enumerate(recommendations):
                tmdb_data = fetch_tmdb_data(rec.get('title', ''))
                with st.container():
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        # Display TMDB poster if available; otherwise use a placeholder
                        image_url = tmdb_data.get('poster_url') if tmdb_data else PLACEHOLDER_IMAGE_URL
                        st.image(image_url, width=150)
                    with col2:
                        title_str = f"{idx+1}. {rec.get('title', 'No Title')}"
                        year_str = f" ({tmdb_data.get('year')})" if tmdb_data and tmdb_data.get('year') else ""
                        st.markdown(f"### {title_str}{year_str}")
                        st.write(rec.get('description', 'No description available.'))
                        st.markdown("**Why you'll like it:**")
                        st.write(rec.get('reasoning', 'No reasoning provided.'))
                st.divider()
        else:
            st.error("Could not retrieve recommendations. Please try again later.")

st.markdown("---")
st.markdown("Built with ❤️ by [Tushar](https://www.linkedin.com/in/tusharnain/) - Mesa School of Business")
