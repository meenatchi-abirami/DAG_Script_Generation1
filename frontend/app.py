# main.py (Streamlit UI)
import streamlit as st
import requests
import uuid
from datetime import datetime
import io

# ---------------------------
# CONFIGURATION
# ---------------------------
API_BASE_URL = "http://localhost:5001/api"

# ---------------------------
# INITIAL SETUP
# ---------------------------
def init_session():
    """Initialize Streamlit session variables."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "history" not in st.session_state:
        st.session_state.history = []
    if "active_session" not in st.session_state:
        st.session_state.active_session = None
    if "generated_dag" not in st.session_state:
        st.session_state.generated_dag = None

# ---------------------------
# FETCH CONVERSATION HISTORY
# ---------------------------
def fetch_all_conversations():
    """Fetch all previous conversations from backend."""
    try:
        response = requests.get(f"{API_BASE_URL}/conversations")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                st.session_state.history = data["conversations"]
            else:
                st.warning("No conversation history found.")
        else:
            st.error("Failed to fetch conversation history.")
    except Exception as e:
        st.error(f"Error fetching history: {e}")

def load_conversation(session_id):
    """Load all messages for a given session."""
    try:
        response = requests.get(f"{API_BASE_URL}/chat_history", params={"session_id": session_id})
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                st.session_state.messages = data["messages"]
                st.session_state.session_id = session_id
                st.session_state.active_session = session_id
                st.session_state.generated_dag = None
                for msg in reversed(data["messages"]):
                    if msg["message_type"] == "system" and "def " in msg["content"]:
                        st.session_state.generated_dag = msg["content"]
                        break
            else:
                st.warning("No messages in this conversation.")
        else:
            st.error("Failed to load conversation.")
    except Exception as e:
        st.error(f"Error loading conversation: {e}")

# ---------------------------
# DISPLAY CHAT MESSAGES
# ---------------------------
def display_chat_history():
    """Display chat messages in the chat area."""
    for message in st.session_state.messages:
        with st.chat_message(message["message_type"]):
            if message["message_type"] == "system" and "def " in message["content"]:
                st.code(message["content"], language="python")
            else:
                st.markdown(message["content"])

# ---------------------------
# DOWNLOAD DAG SCRIPT
# ---------------------------
def download_dag_button(dag_script: str):
    """Show download button for DAG script."""
    buffer = io.BytesIO(dag_script.encode("utf-8"))
    st.download_button(
        label="⬇️ Download DAG Script",
        data=buffer,
        file_name=f"generated_dag_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py",
        mime="text/x-python",
        key=f"download_dag_{st.session_state.session_id}"
    )

# ---------------------------
# MAIN APP
# ---------------------------
def main():
    st.set_page_config(page_title="DAG Script Generator", layout="wide")
    st.title("DAG Script Generator")

    init_session()

    # -----------------------
    # SIDEBAR
    # -----------------------
    with st.sidebar:
        st.header("Conversations")

        if st.button("Refresh Conversations"):
            fetch_all_conversations()

        if st.session_state.history:
            for convo in st.session_state.history:
                title = convo.get("title", "Untitled Conversation")
                if st.button(title, key=convo["session_id"]):
                    load_conversation(convo["session_id"])
                    st.experimental_rerun()
        else:
            st.info("No saved conversations yet.")

        st.divider()
        if st.button("Clear Current Chat"):
            st.session_state.messages = []
            st.session_state.generated_dag = None
            st.session_state.active_session = None
            st.session_state.session_id = str(uuid.uuid4())
            st.success("Chat cleared!")

        st.divider()
        st.header("ℹ️ How to Use")
        st.write("""
        1. Describe your DAG requirements:
           - Tasks to perform  
           - Dependencies  
           - Schedule details  
        2. Your input is validated  
        3. If valid → DAG code is generated  
        4. If invalid → Feedback is shown  
        """)

    # -----------------------
    # MAIN CHAT AREA
    # -----------------------
    display_chat_history()

    user_input = st.chat_input("Describe your DAG requirements...")

    if user_input:
        with st.chat_message("user"):
            st.write(user_input)

        st.session_state.messages.append({
            "message_type": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })

        response = requests.post(f"{API_BASE_URL}/validate_input", json={"input": user_input})
        with st.chat_message("system"):
            if response.status_code == 200:
                data = response.json()
                if data.get("valid"):
                    st.success("Input validated successfully!")

                    dag_response = requests.post(
                        f"{API_BASE_URL}/generate_dag",
                        json={"input": user_input, "session_id": st.session_state.session_id}
                    )

                    if dag_response.status_code == 200:
                        dag_data = dag_response.json()
                        dag_script = dag_data["dag_script"]

                        st.code(dag_script, language="python")
                        st.session_state.generated_dag = dag_script

                        st.session_state.messages.append({
                            "message_type": "system",
                            "content": dag_script,
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        st.error("Failed to generate DAG script.")
                        st.session_state.messages.append({
                            "message_type": "system",
                            "content": "Failed to generate DAG script.",
                            "timestamp": datetime.now().isoformat()
                        })
                else:
                    feedback = data.get("feedback") or "Invalid input. Please try again."
                    st.error(f"{feedback}")
                    st.session_state.messages.append({
                        "message_type": "system",
                        "content": f"{feedback}",
                        "timestamp": datetime.now().isoformat()
                    })
            else:
                st.error("Backend error while validating input.")
                st.session_state.messages.append({
                    "message_type": "system",
                    "content": "Backend error while validating input.",
                    "timestamp": datetime.now().isoformat()
                })

    # Persistent DAG download button
    if st.session_state.generated_dag:
        st.divider()
        download_dag_button(st.session_state.generated_dag)

# ---------------------------
# RUN APP
# ---------------------------
if __name__ == "__main__":
    main()