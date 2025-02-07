```markdown

🎬🌟 Chitra the Movie Recommender - Build 1.0
Mesa School of Business - Tushar Nain

 ## Overview

Chitra is a Streamlit web application that helps you discover movies you might love based on your taste in previously watched films.  Powered by the intelligent DeepSeek API for recommendations and enhanced with movie details from TMDB API, Chitra provides a ranked list of movies with posters, release years, descriptions, and reasons why you might enjoy them.

How it Works:

Input Movie & Preference: You tell Chitra a movie you liked and, most importantly, what you liked about it (e.g., "the acting", "the suspense", "the visuals").
DeepSeek Recommendation Engine: Chitra uses the DeepSeek Reasoner API to analyze your input and generate a ranked list of movie recommendations.
TMDB Movie Enrichment: For each recommended movie, Chitra fetches additional details like posters and release years from The Movie Database (TMDB) API to provide a richer and more visual experience.
Ranked & Reasoned Recommendations: You receive a ranked list of movie suggestions, complete with movie posters, release years, brief descriptions, and clear explanations of why each movie is recommended based on your stated preferences.
Features
Intelligent Movie Recommendations: Powered by DeepSeek API for personalized and relevant movie suggestions.
Ranked Output: Recommendations are presented in a ranked list, ordered by relevance (most likely to enjoy first).
Detailed Movie Information: Includes movie posters (when available), release years, and concise descriptions fetched from TMDB API.
Reasoning Provided: Clear explanations for each recommendation, connecting it back to your stated preferences in the input movie.
User-Friendly Interface: Simple and intuitive Streamlit web application, easy to use for anyone looking for movie inspiration.
Error Handling: Graceful handling of API errors and missing movie data, ensuring a smooth user experience.
Try it out!
[Link to Deployed Streamlit App Here]  Click the link above to access the live Chitra Movie Recommender app (once you have deployed it to Streamlit Cloud).

How to Use the App
Using Chitra is easy! Just follow these steps:

Enter a Movie You Liked: In the first text box, type in the title of a movie that you enjoyed watching.
Tell Us What You Liked: In the second text box, specify what you particularly liked about that movie. Be as specific as possible (e.g., "the complex characters", "the thrilling plot twists", "the beautiful cinematography"). The more details you provide, the better Chitra can understand your taste.
Choose Number of Recommendations: Use the slider to select how many movie recommendations you would like to receive (from 1 to 5).
Click "Get Recommendations": Press the "Get Recommendations" button.
Explore Your Movie List: Chitra will process your request and display a ranked list of movie recommendations. For each movie, you will see:
Rank: The position in the recommendation list (1 being the most relevant).
Movie Poster: A visual poster for the movie (if available).
Movie Title and Year: The title of the movie and its release year.
Description: A brief summary of the movie's plot.
Why You Will Like It?: An explanation of why Chitra recommends this movie based on your input preferences.
Local Development Setup
Want to run Chitra locally or contribute to the project? Follow these steps:

Prerequisites:

Python 3.7 or higher
pip (Python package installer)
Steps:

Clone the Repository:

Bash

git clone [repository-url]  # Replace with your GitHub repository URL
cd streamlit-movie-recommender # Or your repository folder name
Set up Environment Variables:

Create a .env file in the root directory of the project.
Add your API keys to the .env file. Important: Do not commit this .env file to a public repository for security reasons.
DEEPSEEK_API_KEY=YOUR_DEEPSEEK_API_KEY_HERE
TMDB_API_KEY=YOUR_TMDB_API_KEY_HERE
Obtain API Keys:
DeepSeek API Key: Sign up at DeepSeek AI to get your API key.
TMDB API Key: Sign up for a free API key at The Movie Database (TMDB).
Install Dependencies:

Bash

pip install -r requirements.txt
Run the Streamlit App:

Bash

streamlit run streamlit_app.py
Access Locally: Open your web browser and go to the URL displayed in the terminal (usually http://localhost:8501).

Deployment to Streamlit Cloud
To deploy Chitra to Streamlit Cloud and make it publicly accessible, follow these steps:

GitHub Repository: Ensure your code is in a public GitHub repository.
Streamlit Cloud Account: Sign up or log in to Streamlit Cloud.
Create a New App: In your Streamlit Cloud dashboard, click on "New app".
Connect to Repository:
Select your GitHub repository, branch (main or master), and specify streamlit_app.py as the main file path.
Set Up Secrets: Crucially, do not hardcode API keys in your code. Instead, configure secrets in Streamlit Cloud:
Go to your app's settings in Streamlit Cloud ("..." menu -> "Edit Secrets").
Add the following secrets in TOML format:
Ini, TOML

DEEPSEEK_API_KEY = "YOUR_DEEPSEEK_API_KEY_HERE"
TMDB_API_KEY = "YOUR_TMDB_API_KEY_HERE"
Replace "YOUR_DEEPSEEK_API_KEY_HERE" and "YOUR_TMDB_API_KEY_HERE" with your actual API keys. Remember to enclose the API key values in double quotes.
Click "Save".
Deploy!: Click the "Deploy!" button in Streamlit Cloud.
Access Live App: Once deployed, Streamlit Cloud will provide you with a public URL to access your live Movie Recommender app.
Built With
Streamlit - For creating the web application interface.
DeepSeek API - Powering the intelligent movie recommendations.
TMDB API - For movie data and posters.
python-dotenv - For managing environment variables during local development.
requests - For making HTTP requests to APIs.
Credits
Built with ❤️ by Tushar Nain - Mesa School of Business

Enjoy discovering new movies with Chitra!


**Remember to:**

*   **Replace `[repository-url]`** with the actual URL of your GitHub repository in the "Local Development Setup" section.
*   **Replace `[Link to Deployed Streamlit App Here]` and `https://your-streamlit-cloud-app-url`** with the actual URL of your deployed Streamlit Cloud app in both the "Try it out!" and "How to Use the App" sections once you deploy your app.
*   **Remove the placeholder text**  `YOUR_DEEPSEEK_API_KEY_HERE` and `YOUR_TMDB_API_KEY_HERE` in the instructions and remind users to get their own API keys and set them up securely.

This README provides a good overview of your application, instructions for users and developers, and the necessary setup information. You can save this content as `README.md` in your GitHub repository.
