# validate_routes.py (unchanged)
from flask import Blueprint, request, jsonify
from config import get_db_connection
from services.reviewer_agent import ReviewerAgent

validate_bp = Blueprint('validate', __name__)

@validate_bp.route('/validate_input', methods=['POST'])
def validate_input():
    try:
        data = request.json
        input_text = data.get('input')
        
        reviewer = ReviewerAgent()
        is_valid, feedback, raw = reviewer.validate(input_text)

        return jsonify({
            'valid': is_valid,
            'feedback': feedback,
            'raw': raw,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

    