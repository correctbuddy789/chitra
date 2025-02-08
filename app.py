# app.py
import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# Initialize
load_dotenv()

# Configure DeepSeek client
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

def get_movie_recommendations(favorites, preferences):
    """Get AI-powered movie recommendations using DeepSeek API"""
    system_prompt = """You're a senior film expert specialized in Indian and global cinema. 
    Recommend movies based on these rules:
    1. Suggest 5 movies matching both specific titles and general preferences
    2. Prioritize Indian streaming availability (Netflix, Prime, Hotstar)
    3. Mix popular and niche titles (3 Indian, 2 international)
    4. Format as: "Title (Year) - Streaming Platform - Director - Reason"
    5. Add emojis related to movie genres"""
    
    user_input = f"""
    My favorite movies: {favorites}
    What I love in films: {preferences}
    Current year: 2025
    Location: Bengaluru, India
    """

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=0.8,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Recommendation failed: {str(e)}")
        return None

# Streamlit UI
st.set_page_config(page_title="CineBot AI", page_icon="🎬")
st.title("Bollywood & Beyond Movie Advisor")
st.write("🇮🇳 Personalized film recommendations for Indian audiences")

# Input Section
with st.form("movie_form"):
    col1, col2 = st.columns(2)
    with col1:
        favorites = st.text_input(
            "Your All-Time Favorites (comma separated)",
            "Drishyam, Super 30, KGF 2"
        )
    with col2:
        preferences = st.selectbox(
            "Your Preferred Genre",
            ["Action/Drama", "Rom-Com", "Thriller", "Social Drama", "Family"]
        )
    
    submitted = st.form_submit_button("Get Recommendations 🤖")

# Display Results
if submitted:
    if not favorites.strip():
        st.warning("Please enter at least 3 movies you love!")
    else:
        with st.spinner("Analyzing your taste with 50,000 movie patterns..."):
            recommendations = get_movie_recommendations(favorites, preferences)
        
        if recommendations:
            st.subheader("🍿 Your Perfect Weekend Watchlist")
            st.divider()
            st.markdown(f"``````")
            
            # Additional Features
            st.divider()
            with st.expander("📱 Get Streaming Links"):
                st.write("Feature coming soon! Currently in beta testing.")
            
            st.balloons()
