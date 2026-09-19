from flask import Blueprint, request, jsonify
from services.chat_service import chat_service
from utils.auth import token_required
from utils.limiter import limiter

chat_bp = Blueprint('chat_bp', __name__)

@chat_bp.route('/chat', methods=['POST'])
@token_required
@limiter.limit("20 per minute")
def chat():
    data = request.get_json()
    query = data.get('message', '')
    
    if not query:
        return jsonify({'response': "I didn't hear anything."}), 400

    try:
        user_id = request.current_user['user_id']
        response = chat_service.process_query(user_id, query)
        return jsonify({'response': response}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
