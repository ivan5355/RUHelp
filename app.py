from flask import Flask, request, jsonify, render_template
from catalog_chatbot import CatalogChatbot

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


if __name__ == '__main__':
    app.run(debug=True, port=5001) 