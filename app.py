import streamlit as st
from dotenv import load_dotenv
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
from typing import Optional, List, Dict
import time

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
TMDB_API_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
PLACEHOLDER_IMAGE_URL = "https://via.placeholder.com/500x750?text=Poster+Not+Available"

# Create a session with retry logic
def create_requests_session():
    session = requests.Session()
    retries = Retry(
        total=3,  # number of retries
        backoff_factor=1,  # wait 1, 2, 4 seconds between retries
        status_forcelist=[408, 429, 500, 502, 503, 504],  # retry on these status codes
    )
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session

def get_tmdb_movie_details(movie_title: str) -> Optional[Dict]:
    """Fetches movie details from TMDB API based on movie title."""
    if not TMDB_API_KEY:
        st.error("TMDB API key not found. Please check your .env file.")
        return None

    search_url = f"{TMDB_API_BASE_URL}/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": movie_title
    }

    session = create_requests_session()
    try:
        response = session.get(search_url, params=params, timeout=(5, 15))  # (connect timeout, read timeout)
        response.raise_for_status()
        data = response.json()

        if data.get('results'):
            movie_data = data['results'][0]
            poster_path = movie_data.get('poster_path')
            year = movie_data.get('release_date', '')[:4] if movie_data.get('release_date') else 'N/A'

            return {
                "poster_url": f"{TMDB_IMAGE_BASE_URL}{poster_path}" if poster_path else PLACEHOLDER_IMAGE_URL, # Use placeholder if no poster
                "year": year
            }
    except requests.exceptions.RequestException as e:
        print(f"TMDB API error for '{movie_title}': {e}")
    except Exception as e:
        print(f"Unexpected error getting TMDB data: {e}")

    return None

def get_movie_recommendations(liked_movie: str, liked_aspect: str, num_recommendations: int) -> Optional[List[Dict]]:
    """Gets movie recommendations from DeepSeek API with TMDB details."""
    if not DEEPSEEK_API_KEY:
        st.error("DeepSeek API key not found. Please check your .env file.")
        return None

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    system_message = """You are a movie recommendation expert. Provide recommendations in valid JSON format."""

    user_message = f"""Based on the movie '{liked_movie}' that the user liked because '{liked_aspect}',
    recommend {num_recommendations} movies, ranked by relevance. Format as JSON with this structure:
    {{
        "recommendations": [
            {{
                "title": "Movie Title",
                "description": "2-3 sentence description",
                "reasoning": "Why someone who liked {liked_aspect} in {liked_movie} would enjoy this"
            }}
        ]
    }}"""

    data = {
        "model": "deepseek-reasoner",
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 1000,
        "temperature": 0.7
    }

    session = create_requests_session()
    max_retries = 3
    retry_delay = 2  # seconds

    for attempt in range(max_retries):
        try:
            with st.spinner(f"Attempt {attempt + 1}/{max_retries}: Getting recommendations..."):
                response = session.post(
                    DEEPSEEK_API_URL,
                    headers=headers,
                    json=data,
                    timeout=(10, 60)  # (connect timeout, read timeout)
                )
                response.raise_for_status()

                response_data = response.json()
                if not response_data.get('choices'):
                    raise ValueError("No recommendations received from API")

                content = response_data['choices'][0]['message']['content']
                # print(f"Raw content from API: {content}")  # Debug: Print raw content

                # Clean the response content and parse JSON.  Try/except for JSON parsing.
                try:
                    content = content.strip()
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.endswith("```"):
                        content = content[:-3]
                    recommendations = json.loads(content)['recommendations']
                except json.JSONDecodeError as e:
                    st.error(f"JSONDecodeError: {e}")
                    st.text("Raw API Response (for debugging):")
                    st.code(content, language="text") # Show the raw response, very helpful for debugging
                    return None  # Exit the function.  No point continuing if JSON is bad.

                # Fetch TMDB details for each recommendation
                final_recommendations = []
                for rec in recommendations:
                    tmdb_details = get_tmdb_movie_details(rec['title'])
                    final_recommendations.append({
                        **rec,
                        "tmdb_details": tmdb_details or {}
                    })

                return final_recommendations

        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                st.warning(f"Request timed out. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                st.error("Failed to get recommendations after multiple attempts. Please try again later.")
        except requests.exceptions.RequestException as e:
            st.error(f"DeepSeek API request failed: {str(e)}")
            return None  # Important:  Return None after an exception, or the caller won't know it failed.
        except (json.JSONDecodeError, ValueError, KeyError) as e:  # Catch KeyError too
            st.error(f"Failed to process API response: {str(e)}")
            st.text("Raw API Response (for debugging):")
            st.code(content, language="text")  # Display the raw response for debugging
            return None  # Exit the function, don't continue
        except Exception as e: #Catch the exception and prevent the crashing of app
            st.error(f"Unexpected error: {str(e)}")
            return None
    return None  # If all retries failed.


# Streamlit UI
st.title("🎬🌟 Chitra the Movie Recommender")

with st.form("movie_form"):
    liked_movie = st.text_input("Enter a movie you liked:")
    liked_aspect = st.text_input("What did you like about this movie?")
    num_recommendations = st.number_input(
        "Number of recommendations:",
        min_value=1,
        max_value=5,
        value=3
    )
    submit_button = st.form_submit_button("Get Recommendations")

if submit_button:
    if not liked_movie or not liked_aspect:
        st.warning("Please enter both a movie you liked and what you liked about it.")
    else:
        recommendations = get_movie_recommendations(liked_movie, liked_aspect, num_recommendations)

        if recommendations:
            st.success("Here are your personalized movie recommendations:")
            for idx, rec in enumerate(recommendations, 1):
                with st.container():
                    col1, col2 = st.columns([1, 3])

                    with col1:
                        poster_url = rec.get('tmdb_details', {}).get('poster_url')
                        st.image(poster_url, width=150)  # No need for the conditional, get_tmdb_movie_details handles it.

                    with col2:
                        year = rec.get('tmdb_details', {}).get('year', '')
                        title_display = f"{rec['title']} ({year})" if year else rec['title']
                        st.markdown(f"### {idx}. {title_display}")
                        st.write(rec['description'])
                        st.markdown("**Why you'll like it:**")
                        st.write(rec['reasoning'])

                    st.divider()

st.markdown("---")
st.markdown("Built with ❤️ by [Tushar](https://www.linkedin.com/in/tusharnain/) - Mesa School of Business")
