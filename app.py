import uuid

import streamlit as st

from memory.runtime import Persistence
from agent.runtime import create_agent

st.set_page_config(
    page_title="AI Customer Support Agent",
    page_icon="🎧",
    layout="centered",
)


# ---------------------------------------------------------------------------
# One-time persistence + compiled graph, cached across reruns
# ---------------------------------------------------------------------------
@st.cache_resource
def get_persistence():
    return Persistence()


persistence = get_persistence()
graph = create_agent(
    checkpointer=persistence.checkpointer,
    store=persistence.store,
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "customer_id" not in st.session_state:
    st.session_state.customer_id = "CUST001"

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Session")

    st.session_state.customer_id = st.text_input(
        "Customer ID",
        value=st.session_state.customer_id,
    )

    st.caption(f"Thread ID: `{st.session_state.thread_id}`")

    if st.button("🆕 New Conversation"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

st.title("🎧 AI Customer Support & Resolution Agent")
st.caption("LangGraph + Gemini + short-term & long-term memory")

# ---------------------------------------------------------------------------
# Render chat history
# ---------------------------------------------------------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------
user_input = st.chat_input("How can I help you today?")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.status("Thinking...", expanded=False) as status:
            try:
                config = {
                    "configurable": {
                        "thread_id": st.session_state.thread_id,
                    }
                }

                result = graph.invoke(
                    {
                        "user_id": st.session_state.customer_id,
                        "user_message": user_input,
                    },
                    config=config,
                )

                response = result.get(
                    "response", "I was unable to generate a response."
                )

                status.update(label="✅ Completed", state="complete")
                st.markdown(response)

                # -------------------------------------------------------
                # SAVE CHAT HISTORY TO STREAMLIT
                # -------------------------------------------------------
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )

                if result.get("requires_human"):
                    ticket = result.get("ticket_data", {})
                    if ticket:
                        st.info(
                            f"Escalated to human support — ticket "
                            f"`{ticket.get('ticket_id', 'N/A')}` created."
                        )

            except Exception as e:
                status.update(label="❌ Agent Error", state="error")
                st.error(str(e))