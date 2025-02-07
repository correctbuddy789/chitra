# 🎬 Chitra - The Movie Recommender

### Build 1.0 | Mesa School of Business | Tushar Nain

## Overview
Chitra is a Streamlit web application that helps you discover movies you might love based on your taste in previously watched films. Powered by the intelligent **DeepSeek API** for recommendations and enriched with movie details from **TMDB API**, Chitra provides a ranked list of movies with posters, release years, descriptions, and reasons why you might enjoy them.

## How It Works

1. **Input Movie & Preference:** You enter a movie you liked and specify what you enjoyed about it (e.g., "the acting", "the suspense", "the visuals").
2. **DeepSeek Recommendation Engine:** Chitra uses the DeepSeek Reasoner API to analyze your input and generate a ranked list of movie recommendations.
3. **TMDB Movie Enrichment:** For each recommended movie, Chitra fetches additional details like posters and release years from The Movie Database (TMDB) API.
4. **Ranked & Reasoned Recommendations:** You receive a ranked list of movie suggestions with posters, release years, descriptions, and explanations tailored to your preferences.

## Features

✅ **Intelligent Movie Recommendations:** Powered by DeepSeek API for personalized suggestions.  
✅ **Ranked Output:** Movies are ranked based on relevance.  
✅ **Detailed Movie Information:** Posters, release years, and descriptions from TMDB API.  
✅ **Reasoning Provided:** Each recommendation includes an explanation based on your input.  
✅ **User-Friendly Interface:** Simple and intuitive Streamlit web application.  
✅ **Error Handling:** Ensures smooth user experience even with missing data or API errors.  

## Try It Out!
🚀 **[Live Demo of Chitra Movie Recommender](#)**  
_(Replace with your actual Streamlit Cloud app URL after deployment.)_

---

## How to Use the App

1. **Enter a Movie You Liked** - Type in a movie title you enjoyed.
2. **Tell Us What You Liked** - Specify what you enjoyed about it (e.g., "the thrilling plot twists", "the beautiful cinematography").
3. **Choose Number of Recommendations** - Select how many movie recommendations you want (1 to 5).
4. **Click "Get Recommendations"** - Chitra processes your input and generates recommendations.
5. **Explore Your Movie List** - For each movie, you'll see:
   - **Rank** - Position in the recommendation list (1 = most relevant).
   - **Movie Poster** - A visual poster (if available).
   - **Movie Title and Year** - The title and release year.
   - **Description** - A brief summary.
   - **Why You Will Like It?** - Explanation based on your input.

---

## Local Development Setup

Want to run Chitra locally or contribute to the project? Follow these steps:

### Prerequisites
- **Python 3.7 or higher**
- **pip** (Python package installer)

### Steps

#### 1️⃣ Clone the Repository:
```bash
git clone <your-github-repo-url>
cd streamlit-movie-recommender
```

#### 2️⃣ Set Up Environment Variables:
Create a `.env` file in the root directory and add:
```ini
DEEPSEEK_API_KEY=YOUR_DEEPSEEK_API_KEY_HERE
TMDB_API_KEY=YOUR_TMDB_API_KEY_HERE
```
🚨 **Do NOT commit this file to a public repository for security reasons!**

#### 3️⃣ Obtain API Keys:
- **DeepSeek API Key:** Sign up at [DeepSeek AI](https://deepseek.com) to get an API key.
- **TMDB API Key:** Sign up at [The Movie Database (TMDB)](https://www.themoviedb.org/) for a free API key.

#### 4️⃣ Install Dependencies:
```bash
pip install -r requirements.txt
```

#### 5️⃣ Run the Streamlit App:
```bash
streamlit run streamlit_app.py
```
🌐 Open your web browser and visit: `http://localhost:8501`

---

## Deployment to Streamlit Cloud

Deploy Chitra to **Streamlit Cloud** for public access:

### Steps:
1. **Push your code** to a public GitHub repository.
2. **Sign up/log in** to [Streamlit Cloud](https://streamlit.io/).
3. **Create a New App** in Streamlit Cloud.
4. **Connect to GitHub** - Select your repository and `streamlit_app.py` as the main file.
5. **Set Up Secrets:** Add API keys securely:
   - Go to "..." menu → "Edit Secrets" in Streamlit Cloud.
   - Add the following:
```ini
DEEPSEEK_API_KEY = "YOUR_DEEPSEEK_API_KEY_HERE"
TMDB_API_KEY = "YOUR_TMDB_API_KEY_HERE"
```
6. **Click "Save" & Deploy!** 🚀
7. **Get Your Public URL** to access Chitra online.

---

## Built With

- **[Streamlit](https://streamlit.io/)** - Web application framework.
- **[DeepSeek API](https://deepseek.com/)** - AI-powered movie recommendations.
- **[TMDB API](https://www.themoviedb.org/)** - Movie data and posters.
- **python-dotenv** - Environment variable management.
- **requests** - API request handling.

---

## Credits
👨‍💻 Built with ❤️ by **Tushar Nain** - Mesa School of Business

Enjoy discovering new movies with Chitra! 🎥🍿
