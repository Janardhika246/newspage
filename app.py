from flask import Flask, render_template, request,  redirect, url_for, jsonify
import requests
import os
import google.generativeai as genai 
from dotenv import load_dotenv
import json


# Load environment variables from .env file
load_dotenv()

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

app = Flask(__name__)

# Set up API keys and endpoints
NEWS_API_KEY = os.getenv('NEWS_API_KEY')  # Replace with your actual News API key
NEWS_API_ENDPOINT = 'https://newsapi.org/v2/everything'
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')  # Replace with your actual Gemini AI API key
GEMINI_API_ENDPOINT = 'https://api.gemini.ai/rewrite'  # Assuming Gemini has a rewrite API


def generate_dynamic_content(prompt):
    try:
        # Use the Gemini API to generate content
        model = genai.GenerativeModel('gemini-1.5-flash',
                              # Set the `response_mime_type` to output JSON
                              generation_config={"response_mime_type": "application/json"})
        response = model.generate_content(prompt)

        # Check if the response contains the text attribute
        if hasattr(response, 'text'):
            return response.text.strip()
        else:
            return "Error: No content generated."

    except Exception as e:
        return f"Error: {str(e)}"

# Route to fetch and rewrite news articles
@app.route('/get_news')
def get_news():
    # Get query parameters for the news API request
    query = request.args.get('q', 'technology')  # Default query is 'technology'
    from_date = request.args.get('from', '2024-10-02')
    sort_by = request.args.get('sortBy', 'popularity')
    limit = int(request.args.get('limit', 10))  # Limit the number of articles

    # Parameters for the News API request
    params = {
        'q': "technology",
        'apiKey': NEWS_API_KEY,
    }

    try:
        # Request news data from the News API
        response = requests.get(NEWS_API_ENDPOINT, params=params)
        response.raise_for_status()
        news_data = response.json()
        # return news_data

        # Check if articles are returned
        if news_data.get('status') != 'ok' or 'articles' not in news_data:
            return jsonify({'error': 'Failed to retrieve news articles.'}), 500

        # Send each news article to Gemini AI for positive rewrite
        rewritten_news = []
        for article in news_data['articles']:
            title = article['title']
            content = article.get('content', '')

            if content:
                # Prepare the context for Gemini with a prompt
                gemini_payload = {
                    'text': content,
                    'prompt': 'Rewrite this news article with a positive tone.'
                }

                positive_content=generate_dynamic_content(str(gemini_payload))
                # gemini_headers = {
                #     'Authorization': f'Bearer {GEMINI_API_KEY}',
                #     'Content-Type': 'application/json'
                # }

                # try:
                #     # Send the request to Gemini API
                #     gemini_response = requests.post(GEMINI_API_ENDPOINT, json=gemini_payload, headers=gemini_headers)
                #     gemini_response.raise_for_status()
                #     positive_content = gemini_response.json().get('rewrittenText', content)
                # except requests.RequestException as e:
                #     positive_content = f'Could not rewrite content due to error: {str(e)}'
            else:
                positive_content = 'No content available for this article.'

            # Append rewritten content to the list
            rewritten_news.append({
                'title': title,
                'positive_content': positive_content,
                'url': article['url'],
                'urlToImage': article.get('urlToImage'),
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

# Route to handle the input form submission
@app.route('/fetch_news', methods=['POST'])
def fetch_news():
    topic = request.form.get('topic')  # Get the topic from the form
    prompt = f"Fetch good news related to the topic: {topic}."
    
    # Generate content using the Gemini API
    news_content = generate_dynamic_content(prompt)

    try:
        # Convert the string response to a JSON object
        news_json = json.loads(news_content)
        return jsonify(news_json)  # Return the generated news in JSON format
    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse generated content as JSON.", "response": news_content})

# Home endpoint with input form
@app.route('/')
def input_form():
    return render_template('form.html')

if __name__ == '__main__':
    app.run(debug=True)
