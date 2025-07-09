import streamlit as st
import openai
import time


# --- OpenAI API Key ---
openai.api_key = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else st.text_input("Enter your OpenAI API Key", type="password")

# --- Assistant ID ---
ASSISTANT_ID = st.secrets.get("ASSISTANT_ID") or st.text_input("Enter your Assistant ID (asst_...)", type="default")

OPENAI_API_KEY = openai.api_key

# --- Set API Key ---
if not OPENAI_API_KEY or not ASSISTANT_ID:
    st.error("Please set OPENAI_API_KEY and ASSISTANT_ID in your .env file.")
    st.stop()

# ✅ Create OpenAI client with v2 header
client = openai.OpenAI(
    api_key=OPENAI_API_KEY,
    default_headers={"OpenAI-Beta": "assistants=v2"}
)

# --- Streamlit UI ---
st.set_page_config(page_title="JudgeGPT Assistant", page_icon="⚖️")
st.title("⚖️ JudgeGPT: Your Legal Consultant")

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Show chat history ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Input ---
user_input = st.chat_input("Ask your legal question...")

if user_input:
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            # 1. Create thread
            thread = client.beta.threads.create()

            # 2. Add message
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_input
            )

            # 3. Run assistant
            run = client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=ASSISTANT_ID
            )

            # 4. Poll for completion
            while run.status not in ["completed", "failed", "cancelled"]:
                time.sleep(1)
                run = client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )

            # 5. Get reply
            if run.status == "completed":
                messages = client.beta.threads.messages.list(thread_id=thread.id)
                assistant_message = messages.data[0].content[0].text.value
                full_response = assistant_message
            else:
                full_response = f"❌ Run failed: {run.status}"

        except Exception as e:
            full_response = f"❌ Error: {str(e)}"

        message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
