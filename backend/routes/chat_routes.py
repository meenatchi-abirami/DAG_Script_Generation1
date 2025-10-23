import pymysql
from flask import Blueprint, request, jsonify
from config import get_db_connection


chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat_history', methods=['GET'])
def get_chat_history():
    try:
        session_id = request.args.get('session_id')
        
        conn = get_db_connection()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("""
                    SELECT message_type, content, timestamp
                    FROM messages m
                    JOIN conversations c ON m.conversation_id = c.conversation_id
                    WHERE c.session_id = %s
                    ORDER BY timestamp ASC
                """, (session_id,))
                messages = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'messages': messages
            })
        finally:
            conn.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500
 
