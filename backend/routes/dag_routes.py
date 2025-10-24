# dag_routes.py
from flask import Blueprint, request, jsonify
from config import get_db_connection
from services.reviewer_agent import ReviewerAgent
from services.dag_generator import DAGGenerator

dag_bp = Blueprint('dag', __name__)

@dag_bp.route('/generate_dag', methods=['POST'])
def generate_dag():
    try:
        data = request.json
        input_text = data.get('input')
        session_id = data.get('session_id')
        
        # First validate the input
        reviewer = ReviewerAgent()
        is_valid, feedback, raw = reviewer.validate(input_text)

        if not is_valid:
            # Store invalid input and feedback in the database
            try:
                conn = get_db_connection()
                try:
                    with conn.cursor() as cursor:
                        # Create or update conversation with title
                        title = input_text[:50] + "..." if len(input_text) > 50 else input_text
                        cursor.execute("""
                            INSERT INTO conversations (session_id, title)
                            VALUES (%s, %s)
                            ON DUPLICATE KEY UPDATE title=%s
                        """, (session_id, title, title))
                        
                        # Store user message
                        cursor.execute("""
                            INSERT INTO messages (conversation_id, message_type, content)
                            VALUES ((SELECT conversation_id FROM conversations WHERE session_id = %s), 'user', %s)
                        """, (session_id, input_text))
                        
                        # Store assistant feedback for invalid input
                        cursor.execute("""
                            INSERT INTO messages (conversation_id, message_type, content)
                            VALUES ((SELECT conversation_id FROM conversations WHERE session_id = %s), 'system', %s)
                        """, (session_id, feedback))
                        
                    conn.commit()
                finally:
                    conn.close()
            except Exception as db_error:
                print(f"Database error (continuing anyway): {db_error}")
            
            return jsonify({
                'success': False,
                'message': feedback,
                'raw': raw
            }), 400
        
        # Generate DAG if input is valid
        generator = DAGGenerator()
        dag_script = generator.generate(input_text)
        
        # Store in database
        try:
            conn = get_db_connection()
            try:
                with conn.cursor() as cursor:
                    # Create or update conversation with title
                    title = input_text[:50] + "..." if len(input_text) > 50 else input_text
                    cursor.execute("""
                        INSERT INTO conversations (session_id, title)
                        VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE title=%s
                    """, (session_id, title, title))
                    
                    # Store user message
                    cursor.execute("""
                        INSERT INTO messages (conversation_id, message_type, content)
                        VALUES ((SELECT conversation_id FROM conversations WHERE session_id = %s), 'user', %s)
                    """, (session_id, input_text))
                    
                    # Store generated DAG
                    cursor.execute("""
                        INSERT INTO messages (conversation_id, message_type, content)
                        VALUES ((SELECT conversation_id FROM conversations WHERE session_id = %s), 'system', %s)
                    """, (session_id, dag_script))
                    
                    cursor.execute("""
                        INSERT INTO generated_dags (conversation_id, dag_script)
                        VALUES ((SELECT conversation_id FROM conversations WHERE session_id = %s), %s)
                    """, (session_id, dag_script))
                    
                conn.commit()
            finally:
                conn.close()
        except Exception as db_error:
            print(f"Database error (continuing anyway): {db_error}")
        
        return jsonify({
            'success': True,
            'dag_script': dag_script
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    