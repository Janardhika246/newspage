import os
from flask import Flask, render_template, request, jsonify
import requests
import google.generativeai as genai
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

app = Flask(__name__)

# Set up API keys and endpoints
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
NEWS_API_ENDPOINT = 'https://newsapi.org/v2/everything'

@app.route('/')
def input_form():
    return render_template('form.html')

def generate_dynamic_content(prompt):
    try:
        # Use the Gemini API to generate content
        model = genai.GenerativeModel('gemini-1.5-flash',
                                      generation_config={"response_mime_type": "application/json"})
        response = model.generate_content(prompt)

        if hasattr(response, 'text'):
            return response.text.strip()
        else:
            return "Error: No content generated."
    except Exception as e:
        return f"Error: {str(e)}"

# Route to fetch and rewrite news articles based on user topic
@app.route('/get_news', methods=['GET'])
def get_news():
    topic = request.args.get('q', 'good news')  # Default query is 'good news'

    # Parameters for the News API request
    params = {
        'q': topic,
        'apiKey': NEWS_API_KEY,
        'sortBy': 'publishedAt',  # Sort by date
        'pageSize': 10  # Limit the number of articles
    }

    try:
        # Request news data from the News API
        response = requests.get(NEWS_API_ENDPOINT, params=params)
        response.raise_for_status()
        news_data = response.json()

        # Check if articles are returned
        if news_data.get('status') != 'ok' or 'articles' not in news_data:
            return jsonify({'error': 'Failed to retrieve news articles.'}), 500

        # Send each news article to Gemini AI for positive rewrite
        rewritten_news = []
        for article in news_data['articles']:
            title = article['title']
            content = article.get('content', '')
            url = article['url']
            urlToImage = article.get('urlToImage')

            if content:
                # Prepare the context for Gemini with a prompt
                positive_content = generate_dynamic_content(content)
            else:
                positive_content = 'No content available for this article.'

            # Append rewritten content to the list
            rewritten_news.append({
                'title': title,
                'positive_content': positive_content,
                'url': url,
                'urlToImage': urlToImage,
                'publishedAt': article.get('publishedAt')
            })

        # Return the rewritten news in JSON format
        return jsonify({'articles': rewritten_news})
    except requests.RequestException as e:
        return jsonify({'error': f'Failed to fetch news. Error: {str(e)}'}), 500

# Route to render the news page
@app.route('/news')
def news():
    return render_template('news.html')

if __name__ == '__main__':
    app.run(debug=True)
