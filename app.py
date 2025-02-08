import streamlit as st
from dotenv import load_dotenv
import os
import requests
import json
import time  # for retry delay

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Changed to GEMINI_API_KEY
TMDB_API_KEY = os.getenv("TMDB_API_KEY") # Load TMDB API Key

# **MODIFIED GEMINI API URL - Replace YOUR_PROJECT_ID with your actual Project ID**
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/projects/YOUR_PROJECT_ID/locations/us-central1/models/gemini-2-flash:generateContent"
TMDB_API_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
PLACEHOLDER_IMAGE_URL = "https://via.placeholder.com/500x750?text=Poster+Not+Available"

DEBUG_MODE = False  # Set to True to enable detailed debugging outputs


def get_tmdb_movie_details(movie_title):
    """Fetches movie details from TMDB API."""
    if not TMDB_API_KEY:
        st.error("TMDB API key not found. Please check your Streamlit Secrets.")
        return None

    search_url = f"{TMDB_API_BASE_URL}/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": movie_title,
    }

    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        data = response.json()
        if data and data["results"]:
            movie_data = data["results"][0]
            poster_path = movie_data.get("poster_path")
            year = movie_data.get("release_date", "N/A")[:4]
            return {
                "poster_url": f"{TMDB_IMAGE_BASE_URL}{poster_path}" if poster_path else None,
                "year": year if year != "N/A" else "N/A",
            }
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching TMDB data for '{movie_title}': {e}")
        return None


def get_movie_recommendations_gemini(liked_movie, liked_aspect, num_recommendations):
    """Gets movie recommendations using Gemini API and TMDB details."""
    if not GEMINI_API_KEY:
        st.error("Gemini API key not found. Please check your Streamlit Secrets.")
        return None

    # API key in query parameters for Gemini
    params = {"key": GEMINI_API_KEY}
    headers = {"Content-Type": "application/json"}

    prompt_content = f"""
    Based on the movie '{liked_movie}' that the user liked because '{liked_aspect}',
    recommend {num_recommendations} movies, **ranked in order of relevance (most relevant first)**.
    For each recommendation, provide:
    - Movie Title:
    - Brief Description: (around 2-3 sentences)
    - Why you recommend it: (Explain why someone who liked '{liked_aspect}' in '{liked_movie}' would enjoy this).

    Format your response as a JSON. The top level should be a list named "recommendations".
    Each item in the list should be a JSON object with keys: "title", "description", and "reasoning".
    Ensure the "recommendations" list is **ordered from most to least relevant.**
    """

    data = {
        "contents": [
            {
                "parts": [{"text": prompt_content}]
            }
        ],
        "generationConfig": { # Gemini specific parameters for controlling generation
            "maxOutputTokens": 1000, # Adjust as needed
            "temperature": 0.9,      # Adjust for creativity vs. focused output
            "topK": 1,
            "topP": 1
        }
    }

    json_response = None
    retry_count = 0
    max_retries = 1

    while retry_count <= max_retries:
        response = None  # Initialize response for error handling

        try:
            response = requests.post(
                GEMINI_API_URL,
                params=params,  # API key as URL parameter
                headers=headers,
                data=json.dumps(data),
                timeout=30,
            )
            response.raise_for_status()
            api_content = response.text

            if DEBUG_MODE:
                st.write(f"Raw API Text Response (Retry {retry_count}):")
                st.text(api_content)

            try:
                json_response = response.json()

                if DEBUG_MODE:
                    st.write(f"Parsed JSON Response (Retry {retry_count}):")
                    st.json(json_response)

                if 'candidates' in json_response and json_response['candidates']: # Gemini response structure
                    if json_response['candidates'][0]['content']['parts'][0]['text']: # Accessing the text content
                        api_content_gemini = json_response['candidates'][0]['content']['parts'][0]['text']

                        try:
                            recommendation_data = json.loads(api_content_gemini) # Parse Gemini's JSON content

                            if 'recommendations' in recommendation_data and isinstance(recommendation_data['recommendations'], list):
                                ranked_recommendations = recommendation_data['recommendations']
                                final_recommendations = []
                                for recommendation in ranked_recommendations:
                                    movie_title = recommendation.get('title')
                                    tmdb_details = get_tmdb_movie_details(movie_title)
                                    final_recommendation = {
                                        **recommendation,
                                        "tmdb_details": tmdb_details or {},
                                    }
                                    final_recommendations.append(final_recommendation)
                                return final_recommendations

                            else:
                                st.error(f"Unexpected Gemini response format: 'recommendations' list not found (Retry {retry_count}).")
                                st.code(api_content_gemini)
                                return None

                        except json.JSONDecodeError as e_inner_json:
                            st.error(f"ERROR: Failed to parse JSON CONTENT from Gemini API (Retry {retry_count}). **Check Gemini's JSON response format.**")
                            st.error(f"JSONDecodeError details (parsing content): {e_inner_json}")
                            st.code(api_content_gemini)
                            return None
                    else:
                        gemini_raw_error = json_response.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'No text content in Gemini response')
                        st.error(f"Gemini API returned empty or unexpected content within 'candidates' (Retry {retry_count}). Raw response text: {gemini_raw_error}")
                        return None

                else:
                    st.error(f"ERROR: Unexpected Gemini API response structure - No 'candidates' array found (Retry {retry_count}).")
                    st.json(json_response)
                    return None


            except json.JSONDecodeError as e_outer_json:
                st.error(f"CRITICAL ERROR: Gemini API response is NOT VALID JSON at the ROOT level! - Retry {retry_count}.")
                st.error(f"The ENTIRE Gemini API response is not valid JSON. Check API endpoint and Gemini API status.")
                st.error(f"JSONDecodeError details (root level parsing): {e_outer_json}")
                st.code(api_content)
                return None

        except requests.exceptions.RequestException as e_request:
            st.error(f"CRITICAL ERROR: Gemini API request COMPLETELY FAILED! - Retry {retry_count}.")
            if isinstance(e_request, requests.exceptions.Timeout):
                st.error(f"Request timed out after 30 seconds. Gemini API might be slow or unavailable.")
            else:
                st.error(f"App could not complete the HTTP request to the Gemini API endpoint.")
                st.error(f"Request exception details: {e_request}")
            if response is not None:
                st.error(f"HTTP Status Code: {response.status_code}")
                st.error(f"Response Headers: {response.headers}")

        retry_count += 1
        if retry_count <= max_retries:
            st.info(f"Retrying Gemini API request (Attempt {retry_count}/{max_retries})...")
            time.sleep(2)

    return None


st.title("🎬🌟 Chitra the Movie Recommender")
st.markdown("Hi, I am Chitra, now powered by Gemini! Tell me a movie you liked and what you liked about it, and I will recommend you some similar movies.")

liked_movie = st.text_input("Enter a movie you liked:")
liked_aspect = st.text_input("What did you like about this movie?:")
num_recommendations = st.number_input("How many recommendations do you want?", min_value=1, max_value=5, value=3)

if st.button("Get Recommendations"):
    if not liked_movie or not liked_aspect:
        st.warning("Please enter both a movie and what you liked about it.")
    else:
        st.info("Thinking hard with Gemini... please wait!")
        recommendations = get_movie_recommendations_gemini(liked_movie, liked_aspect, num_recommendations) # Using Gemini function

        if recommendations:
            st.success("Movie Recommendations (Ranked):")
            for index, recommendation in enumerate(recommendations):
                rank = index + 1
                tmdb_details = recommendation.get("tmdb_details", {})

                col1, col2 = st.columns([1, 3])

                with col1:
                    poster_url = tmdb_details.get("poster_url")
                    if poster_url:
                        st.image(poster_url, width=150)
                    else:
                        st.image(PLACEHOLDER_IMAGE_URL, width=150)

                with col2:
                    st.markdown(f"**Rank {rank}: {recommendation.get('title', 'Movie Title Not Found')}**")
                    year = tmdb_details.get("year", "N/A")
                    year_display = f" ({year})" if year != "N/A" else ""
                    st.markdown(f"*{recommendation.get('title', 'Movie Title Not Found')}*{year_display}")
                    st.write(recommendation.get("description", "Description not available."))
                    st.write(f"*Why you'll like it*: {recommendation.get('reasoning', 'Reasoning not available.')}")
                st.markdown("---")
        else:
            st.error("Failed to get movie recommendations. Please check error messages above.")

st.markdown("Built with ❤️ by [Tushar](https://www.linkedin.com/in/tusharnain/) - Mesa School of Business")
