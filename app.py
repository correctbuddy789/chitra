import streamlit as st
import os
from dotenv import load_dotenv
import time
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional, List, Dict

# --- Load Environment Variables ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# --- API Configuration ---
# Using the Gemini 2.0 Flash model endpoint for improved performance.
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent"

TMDB_API_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
PLACEHOLDER_IMAGE_URL = "https://via.placeholder.com/500x750?text=Poster+Not+Available"

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# --- Helper Functions ---

def create_requests_session() -> requests.Session:
    """Creates a requests session with retry logic."""
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
    """Fetches movie poster URL and release year from TMDB for a given movie title."""
    if not TMDB_API_KEY:
        st.error("TMDB API key not configured.")
        return None

    session = create_requests_session()
    try:
        url = f"{TMDB_API_BASE_URL}/search/movie?api_key={TMDB_API_KEY}&query={movie_title}"
        response = session.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("results"):
            movie = data["results"][0]
            poster_path = movie.get("poster_path")
            year = movie.get("release_date", "").split("-")[0]
            return {
                "poster_url": f"{TMDB_IMAGE_BASE_URL}{poster_path}" if poster_path else None,
                "year": year if year else "N/A",
            }
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"TMDB API Error: {e}")
        return None

def generate_recommendations(liked_movie: str, liked_aspect: str, num_recommendations: int) -> Optional[List[Dict]]:
    """Generates movie recommendations using the Gemini API free tier with a personalized prompt."""
    if not GEMINI_API_KEY:
        st.error("Gemini API key not found. Please check your .env file.")
        return None

    # Revised prompt: personalized language directly addressing "you".
    prompt = (
        f"You are a movie recommendation expert. You know that you enjoyed '{liked_movie}' because you loved '{liked_aspect}'. "
        f"Please recommend {num_recommendations} movies that share similar qualities and would resonate with you. "
        "For each movie, provide a title, a brief 2-3 sentence description, and in the 'reasoning' field, include a personalized explanation that speaks directly to your taste. "
        "Make sure to explicitly reference your love for the aspect you mentioned. "
        "Return your answer strictly as valid JSON in the following format without any additional commentary:\n\n"
        '{\n'
        '  "recommendations": [\n'
        '    {\n'
        '      "title": "Movie Title",\n'
        '      "description": "2-3 sentence description",\n'
        '      "reasoning": "Explain why this movie is a great match for you, referencing your love for \'{liked_aspect}\'"\n'
        '    }\n'
        '  ]\n'
        '}\n'
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ]
    }
    params = {"key": GEMINI_API_KEY}
    
    for attempt in range(MAX_RETRIES):
        try:
            with st.spinner(f"Attempt {attempt + 1}/{MAX_RETRIES}: Doing my Data Dance and fetching recommendations..."):
                response = requests.post(GEMINI_API_URL, params=params, json=payload, timeout=20)
                response.raise_for_status()
                resp_json = response.json()
                # The raw Gemini response is hidden from the user.

                candidates = resp_json.get("candidates")
                if not candidates or not isinstance(candidates, list):
                    st.error("No candidates found in Gemini API response.")
                    return None

                candidate = candidates[0]
                generated_text = ""
                if "content" in candidate and "parts" in candidate["content"]:
                    generated_text = candidate["content"]["parts"][0].get("text", "")
                elif "output" in candidate:
                    generated_text = candidate["output"].get("text", "")
                else:
                    st.error("Unexpected Gemini API response structure.")
                    return None

                if not generated_text.strip():
                    st.error("Empty text received from Gemini API.")
                    return None

                if generated_text.startswith("```"):
                    lines = generated_text.splitlines()
                    cleaned_lines = [line for line in lines if not line.strip().startswith("```")]
                    generated_text = "\n".join(cleaned_lines).strip()

                try:
                    recommendations_json = json.loads(generated_text)
                    recommendations = recommendations_json.get("recommendations")
                    if not recommendations:
                        st.error("JSON response does not contain 'recommendations'.")
                        st.code(generated_text, language='json')
                        return None
                    return recommendations
                except json.JSONDecodeError as decode_error:
                    st.error(f"Failed to decode JSON from Gemini API response: {decode_error}")
                    st.code(generated_text, language='json')
                    return None

        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                st.warning(f"Request failed (attempt {attempt + 1}): {e}. Retrying in {RETRY_DELAY * (2 ** attempt)} seconds...")
                time.sleep(RETRY_DELAY * (2 ** attempt))
            else:
                st.error(f"Failed to get recommendations after multiple retries: {e}")
                return None
    return None

# --- Streamlit App Layout ---

st.title("🎬 Chitra | Your Streaming Sidekick")
st.markdown(
    """
    Welcome to Chitra – your natural language movie recommender!  
    Simply enter a movie you enjoyed and share what you liked about it (for example, the acting, storyline, or cinematography), 
    and we’ll suggest movies that match your tastes.
    
    The more details you provide, the better the recommendations will be. Feel free to describe what you loved about the movie!
    """
)

with st.form("movie_form"):
    liked_movie = st.text_input("Enter a movie you liked:")
    liked_aspect = st.text_input("What did you like about it? (e.g., the acting, storyline, cinematography, etc.)")
    num_recommendations = st.number_input("Number of recommendations:", min_value=1, max_value=10, value=3)
    submit_button = st.form_submit_button("Get Recommendations")

if submit_button:
    if not liked_movie or not liked_aspect:
        st.warning("Please enter both a movie title and details about what you liked.")
    else:
        recommendations = generate_recommendations(liked_movie, liked_aspect, num_recommendations)
        if recommendations:
            st.success("Tada! Here are your personalized movie recommendations:")
            for idx, rec in enumerate(recommendations):
                tmdb_data = fetch_tmdb_data(rec.get("title", ""))
                with st.container():
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if tmdb_data and tmdb_data.get("poster_url"):
                            st.image(tmdb_data["poster_url"], width=150)
                        else:
                            st.markdown(
                                """
                                <div style="width:150px;height:225px;background-color:#ddd;
                                display:flex;align-items:center;justify-content:center;border-radius:8px;">
                                    <span style="color:#555;font-weight:bold;">No Image</span>
                                </div>
                                """, unsafe_allow_html=True
                            )
                    with col2:
                        title_str = f"{idx + 1}. {rec.get('title', 'No Title')}"
                        year_str = f" ({tmdb_data.get('year')})" if tmdb_data and tmdb_data.get("year") else ""
                        st.markdown(f"### {title_str}{year_str}")
                        st.write(rec.get("description", "No description available."))
                        st.markdown("**Why you'll like it:**")
                        st.write(rec.get("reasoning", "No reasoning provided."))
                st.divider()
        else:
            st.error("Could not retrieve recommendations. Please try again later.")

st.markdown("---")
st.markdown("Built with ❤️ by [Tushar](https://www.linkedin.com/in/tusharnain/) - Mesa School of Business")
