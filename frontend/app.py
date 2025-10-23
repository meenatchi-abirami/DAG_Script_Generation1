import streamlit as st
import requests
import uuid
from datetime import datetime
import io

# Constants
API_BASE_URL = "http://localhost:5001/api"

# ----------------------------
# Session Initialization
# ----------------------------
def init_session():
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'history' not in st.session_state:
        st.session_state.history = []

# ----------------------------
# Fetch Chat History from Backend
# ----------------------------
def get_chat_history():
    response = requests.get(
        f"{API_BASE_URL}/chat_history",
        params={"session_id": st.session_state.session_id}
    )
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            st.session_state.history = data["messages"]

# ----------------------------
# Display Previous Chat History (in Chat Area)
# ----------------------------
def display_chat_history():
    for message in st.session_state.messages:
        with st.chat_message(message["message_type"]):
            st.write(message["content"])

# ----------------------------
# Sidebar - Chat History
# ----------------------------
def display_sidebar_history():
    st.header("Previous Sessions 🕒")
    if st.session_state.history:
        for msg in reversed(st.session_state.history):
            with st.expander(f"{msg['timestamp'][:19]} - {msg['message_type'].capitalize()}"):
                st.markdown(f"**{msg['message_type'].capitalize()}:** {msg['content']}")
    else:
        st.info("No previous chat history found.")

# ----------------------------
# DAG Script Download
# ----------------------------
def download_dag_button(dag_script: str):
    buffer = io.BytesIO()
    buffer.write(dag_script.encode('utf-8'))
    buffer.seek(0)
    st.download_button(
        label="⬇️ Download DAG Script",
        data=buffer,
        file_name=f"generated_dag_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py",
        mime="text/x-python"
    )

# ----------------------------
# Main Streamlit App
# ----------------------------
def main():
    st.set_page_config(page_title="DAG Script Generator", layout="wide")
    st.title("🧠 DAG Script Generator")

    # Initialize session
    init_session()

    # Sidebar Information
    with st.sidebar:
        st.header("How to Use 🧩")
        st.write("""
        1. Describe your DAG requirements including:
           - Tasks to perform  
           - Dependencies  
           - Schedule info  
        2. Input is validated first  
        3. If valid, DAG script is generated automatically
        """)

        # Load and display previous chat history
        if st.button("🔄 Load Previous History"):
            get_chat_history()

        display_sidebar_history()

        # Clear chat history
        if st.button("🧹 Clear Current Chat"):
            st.session_state.messages = []
            st.success("Chat cleared!")

    # Display chat history in main area
    display_chat_history()

    # Input text
    user_input = st.chat_input("Describe your DAG requirements...")

    if user_input:
        # Display user message
        with st.chat_message("user"):
            st.write(user_input)

        # Save to current session messages
        st.session_state.messages.append({
            "message_type": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })

        # Validate input
        response = requests.post(
            f"{API_BASE_URL}/validate_input",
            json={"input": user_input}
        )

        with st.chat_message("assistant"):
            if response.status_code == 200:
                data = response.json()
                score = data.get('raw', {}).get('score')

                if score is not None:
                    st.write(f"Validation score: {score}")

                if data["valid"]:
                    st.success("✅ Input validated successfully!")

                    # Generate DAG
                    dag_response = requests.post(
                        f"{API_BASE_URL}/generate_dag",
                        json={
                            "input": user_input,
                            "session_id": st.session_state.session_id
                        }
                    )

                    if dag_response.status_code == 200:
                        dag_data = dag_response.json()
                        dag_script = dag_data["dag_script"]

                        st.code(dag_script, language="python")

                        # Add download button
                        download_dag_button(dag_script)

                        # Add to message history
                        st.session_state.messages.append({
                            "message_type": "assistant",
                            "content": dag_script,
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        err = dag_response.json() if dag_response.content else {'error': 'Unknown error'}
                        st.error(f"❌ Failed to generate DAG script: {err}")
                else:
                    feedback = data.get("feedback") or data.get('raw') or 'No feedback'
                    st.error(f"❌ Input validation failed: {feedback}")

                    st.session_state.messages.append({
                        "message_type": "assistant",
                        "content": f"Input validation failed: {feedback}",
                        "timestamp": datetime.now().isoformat()
                    })
            else:
                st.error("⚠️ Error processing request")

# ----------------------------
# Run App
# ----------------------------
if __name__ == "__main__":
    main()
