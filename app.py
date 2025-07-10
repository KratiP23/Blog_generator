from flask import Flask, request, jsonify
import http.client
import json
from groq import Groq
from dotenv import load_dotenv
import os 

load_dotenv()

app = Flask(__name__)

SERPER_API_KEY = os.getenv('SERPER_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

groq_client = Groq(api_key=GROQ_API_KEY)

def fetch_latest_news(title):

    conn = http.client.HTTPSConnection("google.serper.dev")
    payload = json.dumps({
    "q": title,
    "gl": "in"
    })
    headers = {
    'X-API-KEY': SERPER_API_KEY ,
    'Content-Type': 'application/json'
    }
    conn.request("POST", "/news", payload, headers)
    res = conn.getresponse()
    data = json.loads(res.read().decode("utf-8"))
    output = data.get("news")
    print(output)
    return output

def generate_blog(news, user_input, news_title):
    """
    Generate a personalized blog post based on news articles and user preferences.
    
    Args:
        news (list): List of news articles with title, snippet, source, etc.
        user_input (dict): User preferences with tone, style, target audience, etc.
        news_title (str): Main title/topic of the news being covered
    
    Returns:
        str: Generated blog content
    """
    # Extract key information from news articles
    news_titles = [article.get('title', '') for article in news if 'title' in article]
    news_snippets = [article.get('snippet', '') for article in news if 'snippet' in article]
    sources = [article.get('source', '') for article in news if 'source' in article]
    unique_sources = list(set(sources))
    
    # Determine dominant emotion from news content
    emotion_indicators = {
        'positive': ['success', 'achievement', 'relief', 'hail', 'satisfaction', 'praise'],
        'negative': ['tension', 'war', 'arrest', 'attack', 'fear', 'threat', 'terror'],
        'neutral': ['report', 'announce', 'state', 'inform', 'reveal'],
        'urgent': ['breaking', 'alert', 'urgent', 'critical', 'immediate']
    }
    
    # Count emotion indicators in titles and snippets
    emotion_counts = {emotion: 0 for emotion in emotion_indicators}
    combined_text = ' '.join(news_titles + news_snippets).lower()
    
    for emotion, indicators in emotion_indicators.items():
        for indicator in indicators:
            if indicator.lower() in combined_text:
                emotion_counts[emotion] += 1
    
    # Determine dominant emotion
    dominant_emotion = max(emotion_counts, key=emotion_counts.get)
    if emotion_counts[dominant_emotion] == 0:
        dominant_emotion = 'neutral'  # Default if no indicators found
    
    # Extract user preferences with defaults
    tone = user_input.get('tone', 'informative')
    perspective = user_input.get('perspective', 'balanced')
    audience = user_input.get('audience', 'general')
    humor_level = user_input.get('humor_level', 'moderate')
    
    # Adjust humor based on dominant emotion
    if dominant_emotion == 'negative' and humor_level != 'none':
        humor_level = 'subtle'  # Reduce humor for sensitive topics
    
    prompt = f"""
    Write a high-quality, creative blog post about "{news_title}" based on recent news.
    
    Here's what I know about the topic from {len(news)} news articles from sources including {', '.join(unique_sources[:3])}{' and others' if len(unique_sources) > 3 else ''}:
    
    Key points from headlines:
    - {news_titles[0] if news_titles else 'No headlines available'}
    {('- ' + news_titles[1]) if len(news_titles) > 1 else ''}
    {('- ' + news_titles[2]) if len(news_titles) > 2 else ''}
    
    Content guidelines:
    - Tone: {tone} (while matching the {dominant_emotion} emotion of the news)
    - Perspective: {perspective}
    - Target audience: {audience}
    - Humor level: {humor_level} (appropriate to topic sensitivity)
    
    Writing style:
    - Use a conversational, human-like writing style
    - Include thoughtful analysis that connects the facts
    - Vary sentence structure and paragraph length for readability
    - Use analogies or metaphors where appropriate
    - Create an engaging headline that captures attention
    - Open with a compelling hook
    - Close with a thought-provoking conclusion or call to action
    - Total length: 800-1000 words
    
    The blog should feel like it was written by an expert human writer with a distinct voice, not generic AI-generated content. Make it engaging, insightful, and worthy of being shared.
    """
    
    print(f'Prompt: {prompt}')
    
    completion = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are an expert blog writer with years of experience in journalism and content creation. You craft engaging, insightful pieces that balance informative reporting with a distinctive voice. Your writing is known for its clarity, creativity, and human-like quality."},
            {"role": "user", "content": prompt}
        ],
    )
    
    print(f'Completion received')
    return completion.choices[0].message.content

@app.route('/generate_blog', methods=['POST'])
def generate_blog_route():
    data = request.json
    title = data.get('title')
    user_input = data.get('user_input')

    if not title and user_input:
        return jsonify({'error': 'Missing fields'}), 400

    try:
        news = fetch_latest_news(title)
        blog = generate_blog(news, user_input, title)
        return {"blog": blog}
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)