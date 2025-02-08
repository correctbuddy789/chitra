import streamlit as st
from dotenv import load_dotenv
import os
import requests
import json

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"  # Replace with actual DeepSeek Reasoner API endpoint if different

def get_movie_recommendations(liked_movie, liked_aspect, num_recommendations):
    """
    Calls the DeepSeek API to get movie recommendations, requesting them to be ranked.

    Args:
        liked_movie (str): Movie the user liked.
        liked_aspect (str): What the user liked about the movie.
        num_recommendations (int): Number of movie recommendations to generate.

    Returns:
        list: Ranked list of movie recommendations (dictionaries) or None if error.
    """
    if not DEEPSEEK_API_KEY:
        st.error("DeepSeek API key not found. Please check your .env file.")
        return None

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
    Based on the movie '{liked_movie}' that the user liked because '{liked_aspect}',
    please recommend {num_recommendations} movies, *ranked in order of relevance (most relevant first)*.
    For each recommendation, provide:
    - Movie Title:
    - Brief Description: (around 2-3 sentences)
    - Why you recommend it: (Explain clearly and concisely why someone who liked '{liked_aspect}' in '{liked_movie}' would enjoy this specific recommendation).

    Format your response as a JSON. The top level should be a list named "recommendations".
    Each item in the list should be a JSON object with keys: "title", "description", and "reasoning".
    Ensure the "recommendations" list is *ordered from most to least relevant.*
    """

    data = {
        "model": "deepseek-reasoner", # Or the specific model name you are using
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000, # Adjust as needed
        "n": 1,
        "stop": ["\nJSON"] # Assuming JSON format, adjust stop sequence if needed
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, data=json.dumps(data))
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        json_response = response.json()

        # --- REMOVE DEBUGGING OUTPUT  ---
        # st.write("Raw API Response (for debugging):") # Debugging line removed
        # st.json(json_response) # Debugging line removed
        # --- END REMOVE DEBUGGING OUTPUT ---


        # Assuming the response structure contains choices, and then messages, and content
        if 'choices' in json_response and json_response['choices']:
            api_content = json_response['choices'][0]['message']['content']

            # --- REMOVE MARKDOWN WRAPPERS ---
            api_content = api_content.replace("json", "").replace("", "").strip()
            # --- END REMOVE MARKDOWN WRAPPERS ---


            # --- Attempt to parse JSON from the response content ---
            try:
                recommendation_data = json.loads(api_content)

                if 'recommendations' in recommendation_data and isinstance(recommendation_data['recommendations'], list):
                    return recommendation_data['recommendations'] # Now returning the ranked list directly
                else:
                    st.error("Unexpected JSON structure in API response: 'recommendations' list not found.")
                    return None

            except json.JSONDecodeError as e:
                st.error(f"Error decoding JSON response from API after removing wrappers: {e}")
                st.code(api_content) # Display the raw content for debugging
                return None

        else:
            st.error("Unexpected response structure from API: No 'choices' found.")
            return None


    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
        return None


st.title("Movie Recommendation App")

liked_movie = st.text_input("Enter a movie you liked:")
liked_aspect = st.text_input("What did you like about this movie (e.g., 'the actors', 'the suspense', 'the visuals')?:")
num_recommendations = st.number_input("How many movie recommendations do you want?", min_value=1, max_value=5, value=3) # You can adjust max_value

if st.button("Get Recommendations"):
    if not liked_movie or not liked_aspect:
        st.warning("Please enter both a movie you liked and what you liked about it.")
    else:
        st.info("Doing the Movie Dance... Please wait.")
        recommendations = get_movie_recommendations(liked_movie, liked_aspect, num_recommendations)

        if recommendations:
            st.success("Tada, Check these below:")
            for index, recommendation in enumerate(recommendations): # Enumerate for ranked list
                rank = index + 1 # Rank starts from 1
                st.markdown(f"*Rank {rank}: {recommendation.get('title', 'Movie Title Not Found')}*") # Bold title with rank
                st.write(recommendation.get('description', 'Description not available.'))
                st.write(f"Why I think you will like it?: {recommendation.get('reasoning', 'Reasoning not available.')}")
                st.markdown("---") # Separator

        else:
            st.error("Failed to get movie recommendations. Please check the error messages above.”)
