from flask import Flask, request, jsonify, render_template
from catalog_chatbot import CatalogChatbot, health_check

app = Flask(__name__)
chatbot = CatalogChatbot()

@app.route('/')
def home():
    return render_template('catalog_chat.html')

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    try:
        data = request.get_json()
        user_query = (data.get('query') or '').strip()
        
        if not user_query:
            return jsonify({'error': 'Please provide a query'}), 400

        result = chatbot.chat(user_query)
        return jsonify({'response': result['response'], 'sources': result.get('sources', [])})

    except Exception:
        return jsonify({'error': 'An error occurred processing your request'}), 500


@app.route('/health/keys', methods=['GET'])
def health_keys():
    """Lightweight endpoint to verify API key configuration and connectivity."""
    status = health_check()
    http_code = 200 if (status.get('google', {}).get('ok') and status.get('pinecone', {}).get('ok')) else 503
    return jsonify(status), http_code


if __name__ == '__main__':
    app.run(debug=True, port=5001) 