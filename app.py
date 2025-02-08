import streamlit as st
from dotenv import load_dotenv
import os
import requests
import json
import time  # for retry delay

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY") # Load TMDB API Key

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
TMDB_API_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500" # You can adjust image size if needed
PLACEHOLDER_IMAGE_URL = "https://via.placeholder.com/500x750?text=Poster+Not+Available" # Placeholder image URL


def get_tmdb_movie_details(movie_title):
    """
    Fetches movie details from TMDB API based on movie title.

    Args:
        movie_title (str): Title of the movie to search for.

    Returns:
        dict: Dictionary containing TMDB details (poster_path, year) or None if not found/error.
    """
    if not TMDB_API_KEY:
        st.error("TMDB API key not found. Please check your .env file.")
        return None

    search_url = f"{TMDB_API_BASE_URL}/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": movie_title
    }

    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status() # Raise HTTPError for bad responses
        data = response.json()

        if data and data['results']:
            movie_data = data['results'][0] # Take the first result, assuming best match
            poster_path = movie_data.get('poster_path')
            year = movie_data.get('release_date', 'N/A')[:4] # Get year from release date, default 'N/A'

            return {
                "poster_url": f"{TMDB_IMAGE_BASE_URL}{poster_path}" if poster_path else None, # Construct full image URL
                "year": year if year != 'N/A' else 'N/A',
            }
        else:
            return None # Movie not found on TMDB

    except requests.exceptions.RequestException as e:
        print(f"Error fetching TMDB data for '{movie_title}': {e}") # Log error, but don't show error to user for missing TMDB data
        return None



def get_movie_recommendations(liked_movie, liked_aspect, num_recommendations):
    """
    Calls the DeepSeek API to get ranked movie recommendations and fetches TMDB details for each.

    Args:
        liked_movie (str): Movie the user liked.
        liked_aspect (str): What the user liked about the movie.
        num_recommendations (int): Number of movie recommendations to generate.

    Returns:
        list: Ranked list of movie recommendations (dictionaries) with DeepSeek and TMDB data, or None if error.
    """
    # ... (DeepSeek API call - same as in the previous corrected version) ...
    if not DEEPSEEK_API_KEY: # ... (API Key Check - same as before) ...
        st.error("DeepSeek API key not found. Please check your .env file.")
        return None

    headers = { # ... (Headers - same as before) ...
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f""" # ... (Prompt - same as in the ranked version) ...
    Based on the movie '{liked_movie}' that the user liked because '{liked_aspect}',
    please recommend {num_recommendations} movies, **ranked in order of relevance (most relevant first)**.
    For each recommendation, provide:
    - Movie Title:
    - Brief Description: (around 2-3 sentences)
    - Why you recommend it: (Explain clearly and concisely why someone who liked '{liked_aspect}' in '{liked_movie}' would enjoy this specific recommendation).

    Format your response as a JSON. The top level should be a list named "recommendations".
    Each item in the list should be a JSON object with keys: "title", "description", and "reasoning".
    Ensure the "recommendations" list is **ordered from most to least relevant.**
    """

    data = { # ... (Data payload - same as before) ...
        "model": "deepseek-reasoner", # Or the specific model name you are using
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000, # Adjust as needed
        "n": 1,
        "stop": ["\nJSON"] # Assuming JSON format, adjust stop sequence if needed
    }

    json_response = None # Initialize json_response outside try block
    retry_count = 0
    max_retries = 1 # Let's try one retry

    while retry_count <= max_retries: # Retry loop

        try: # --- Outer try block for the *entire* API request process ---
            response = requests.post(DEEPSEEK_API_URL, headers=headers, data=json.dumps(data), timeout=15) # **NEW: Timeout added**
            response.raise_for_status() # Raise HTTPError for bad responses

            api_content = response.text # Get raw text content - BEFORE trying to parse JSON

            # --- Debugging: Show raw API text response ---
            st.write(f"Raw API Text Response (for debugging - BEFORE JSON parsing) - Retry {retry_count}:")
            st.text(api_content)
            # --- End Debugging ---

            try: # --- Inner try block ONLY for JSON parsing ---
                json_response = response.json() # Now try to parse JSON

                # --- Debugging: Show parsed JSON (if parsing successful) ---
                st.write(f"Parsed JSON Response (for debugging - if JSON parsing succeeded) - Retry {retry_count}:")
                st.json(json_response)
                # --- End Debugging ---

                if 'choices' in json_response and json_response['choices']:
                    api_content = json_response['choices'][0]['message']['content']

                    if not api_content: # **NEW: Check for empty api_content**
                        st.error(f"DeepSeek API returned an empty content response within 'choices' - Retry {retry_count}.")
                        return None

                    api_content = api_content.replace("`json", "").replace("`", "").strip() # Clean up wrappers

                    try: # --- Innermost try block for JSON parsing of api_content ---
                        recommendation_data = json.loads(api_content) # Parse JSON content

                        if 'recommendations' in recommendation_data and isinstance(recommendation_data['recommendations'], list):
                            ranked_recommendations = recommendation_data['recommendations'] # Get ranked recommendations list

                            # --- Fetch TMDB details for each recommendation ---
                            final_recommendations = []
                            for recommendation in ranked_recommendations:
                                movie_title = recommendation.get('title')
                                tmdb_details = get_tmdb_movie_details(movie_title) # Fetch TMDB details

                                # Merge DeepSeek recommendation with TMDB details
                                final_recommendation = {
                                    **recommendation, # Keep DeepSeek recommendation data
                                    "tmdb_details": tmdb_details or {} # Add TMDB details (or empty dict if None)
                                }
                                final_recommendations.append(final_recommendation)

                        return final_recommendations # Return list of recommendations with merged data
                    else:
                        st.error(f"Unexpected API response format: 'recommendations' list not found in JSON content - Retry {retry_count}.")
                        st.code(api_content) # Show raw content for inspection
                        return None

                except json.JSONDecodeError as e_inner_json: # ... (Innermost JSON Error Handling - for api_content parsing) ...
                    st.error(f"ERROR: Failed to parse JSON CONTENT from DeepSeek API (within 'choices') - Retry {retry_count} - **Likely cause: Typo in movie title or unrecognized movie by API.**") # Added typo hint
                    st.error(f"This means the 'content' part of the API response, expected to be JSON, is not valid JSON.")
                    st.error(f"JSONDecodeError details (parsing content): {e_inner_json}")
                    st.code(api_content) # Display the raw CONTENT that FAILED to parse
                    return None


                else: # ... (No Choices Error Handling - Improved message) ...
                    st.error(f"ERROR: Unexpected DeepSeek API response structure - No 'choices' array found at top level - Retry {retry_count}.")
                    st.error(f"The API response is missing the top-level 'choices' array. This is unexpected structure.")
                    st.json(json_response) # Show the full json_response for debugging structure
                    return None


            # If we reach here without errors in the inner try blocks, it was successful! Break out of retry loop.
            break # Success! Exit retry loop

        except json.JSONDecodeError as e_outer_json: # --- Outer JSON Error Handling - for response.json() parsing ---
            st.error(f"CRITICAL ERROR: DeepSeek API response is NOT VALID JSON at the ROOT level! - Retry {retry_count} - **Likely cause: Typo in movie title or unrecognized movie may lead to API returning non-JSON error page.**") # Added typo hint
            st.error(f"The entire API response is not valid JSON. This is a major problem. Check API endpoint, headers, and DeepSeek API status.")
            st.error(f"JSONDecodeError details (root level parsing): {e_outer_json}")
            st.code(api_content) # Display the raw TEXT response that FAILED to parse at root level

        except requests.exceptions.RequestException as e_request: # --- Request Exception Handling - Network or HTTP errors ---
            st.error(f"CRITICAL ERROR: DeepSeek API request COMPLETELY FAILED! - Retry {retry_count}.")
            st.error(f"The app could not even complete the HTTP request to the DeepSeek API endpoint. This is likely a network issue, incorrect API endpoint URL, or a problem preventing connection.")
            st.error(f"Request exception details: {e_request}") # Show specific request exception details
            if response is not None: # **NEW: Log status code and headers if response object exists**
                st.error(f"HTTP Status Code: {response.status_code}")
                st.error(f"Response Headers: {response.headers}")


        retry_count += 1
        if retry_count <= max_retries:
            st.info(f"Retrying DeepSeek API request (Attempt {retry_count}/{max_retries})...")
            time.sleep(2) # Wait for 2 seconds before retrying

    return None # Return None if all retries failed or any other error occurred


st.title("🎬🌟 Chitra the Movie Recommender")

liked_movie = st.text_input("Enter a movie you liked:")
liked_aspect = st.text_input("What did you like about this movie (e.g., 'the actors', 'suspense', 'visuals')?:")
num_recommendations = st.number_input("How many movie recommendations do you want?", min_value=1, max_value=5, value=3)

if st.button("Get Recommendations"):
    if not liked_movie or not liked_aspect:
        st.warning("Please enter both a movie you liked and what you liked about it.The more you tell me, the better recommendations I can give you!")
    else:
        st.info("Doing a Data Dance... Please wait, can take upto 1 Minute (Need to make sure, you get the best recommendations!)")
        recommendations = get_movie_recommendations(liked_movie, liked_aspect, num_recommendations)

        if recommendations:
            st.success("Movie Recommendations (Ranked):")
            for index, recommendation in enumerate(recommendations):
                rank = index + 1
                tmdb_details = recommendation.get('tmdb_details', {}) # Safely get TMDB details

                col1, col2 = st.columns([1, 3]) # Adjust column ratio as needed

                with col1:
                    poster_url = tmdb_details.get('poster_url')
                    if poster_url:
                        st.image(poster_url, width=150) # Display poster, adjust width as needed
                    else:
                        st.image(PLACEHOLDER_IMAGE_URL, width=150) # Placeholder if no poster

                with col2:
                    st.markdown(f"**Rank {rank}: {recommendation.get('title', 'Movie Title Not Found')}**")
                    year = tmdb_details.get('year', 'N/A')
                    year_display = f" ({year})" if year != 'N/A' else "" # Add year in parenthesis if available
                    st.markdown(f"*{recommendation.get('title', 'Movie Title Not Found')}*{year_display}") # Italic title with year

                    st.write(recommendation.get('description', 'Description not available.'))
                    st.write(f"*Why you will like it?*: {recommendation.get('reasoning', 'Reasoning not available.')}")


                st.markdown("---")
        else:
            st.error("Failed to get movie recommendations. Please check the error messages above.")

st.markdown("Built with ❤️ by [Tushar](https://www.linkedin.com/in/tusharnain/) - Mesa School of Business")
