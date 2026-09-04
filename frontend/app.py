import streamlit as st
import requests
import uuid

# ------------------------------------
# Configuration
# ------------------------------------

st.set_page_config(
    page_title="FinanceAI",
    page_icon="💰",
    layout="wide"
)

FASTAPI_URL = "http://localhost:8000"

# ------------------------------------
# CSS
# ------------------------------------

st.markdown("""
<style>

.stApp {
    background-color: #0b0f14;
    color: #f5f7fa;
}

/* Sidebar */

section[data-testid="stSidebar"] {
    background-color: #0f141b;
    border-right: 1px solid #202833;
}

/* Brand */

.brand {
    font-size: 22px;
    font-weight: 700;
    color: white;
    margin-bottom: 35px;
}

/* Hero */

.hero {
    text-align: center;
    padding: 45px 20px 25px;
}

.hero h1 {
    color: white;
    font-size: 38px;
    margin-bottom: 8px;
}

.hero p {
    color: #8b949e;
    font-size: 16px;
}

/* AI message */

.ai-message {
    background: #151b23;
    border: 1px solid #252d38;
    border-radius: 16px;
    padding: 18px 20px;
    margin: 12px 0 22px;
    line-height: 1.6;
}

/* User message */

.user-message {
    background: #166534;
    border-radius: 16px;
    padding: 15px 18px;
    margin: 12px 0 22px auto;
    max-width: 75%;
    line-height: 1.5;
}

/* Message label */

.message-label {
    font-size: 13px;
    font-weight: 600;
    color: #9ca3af;
    margin-bottom: 8px;
}

/* Disclaimer */

.disclaimer {
    text-align: center;
    color: #66717e;
    font-size: 11px;
    margin-top: 20px;
    padding-bottom: 20px;
}

</style>
""", unsafe_allow_html=True)

# ------------------------------------
# Session state
# ------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())

# ------------------------------------
# Sidebar
# ------------------------------------

with st.sidebar:

    st.markdown(
        '<div class="brand">💰 FinanceAI</div>',
        unsafe_allow_html=True
    )

    if st.button(
        "＋ New conversation",
        use_container_width=True
    ):
        st.session_state.messages = []
        st.session_state.conversation_id = str(uuid.uuid4())
        st.rerun()

    st.markdown("---")

    st.markdown("### AI Settings")

    model = st.selectbox(
        "Model",
        [
            "FinanceAI Pro",
            "FinanceAI Fast",
            "FinanceAI Research"
        ]
    )

    st.markdown("---")

    st.caption(
        "AI-generated information. "
        "Not financial advice."
    )

# ------------------------------------
# Header
# ------------------------------------

st.markdown("""
<div class="hero">

<h1>💰 Finance AI Assistant</h1>

<p>
Ask questions about markets, stocks,
investments and financial concepts.
</p>

</div>
""", unsafe_allow_html=True)

# ------------------------------------
# Suggested prompts
# ------------------------------------

if not st.session_state.messages:

    st.markdown(
        "<p style='text-align:center;color:#8b949e'>"
        "Try asking"
        "</p>",
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(
            "📈 Analyze a stock",
            use_container_width=True
        ):
            st.session_state.messages.append({
                "role": "user",
                "content": "Analyze Apple stock"
            })
            st.rerun()

    with col2:
        if st.button(
            "⚖️ Compare investments",
            use_container_width=True
        ):
            st.session_state.messages.append({
                "role": "user",
                "content": "Compare stocks and bonds"
            })
            st.rerun()

    with col3:
        if st.button(
            "🧠 Explain investing",
            use_container_width=True
        ):
            st.session_state.messages.append({
                "role": "user",
                "content": "Explain compound interest"
            })
            st.rerun()

# ------------------------------------
# Display messages
# ------------------------------------

for message in st.session_state.messages:

    content = message["content"].replace(
        "\n",
        "<br>"
    )

    if message["role"] == "assistant":

        st.markdown(
            f"""
            <div class="ai-message">

                <div class="message-label">
                    🤖 FinanceAI
                </div>

                {content}

            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            f"""
            <div class="user-message">

                <div class="message-label">
                    You
                </div>

                {content}

            </div>
            """,
            unsafe_allow_html=True
        )

# ------------------------------------
# Call FastAPI
# ------------------------------------

def call_fastapi(message: str):

    payload = {
        "question": message,
        # "conversation_id":
        #     st.session_state.conversation_id
    }

    try:

        response = requests.post(
            f"{FASTAPI_URL}/ask",
            json=payload,
            timeout=60
        )

        response.raise_for_status()

        data = response.json()

        return data["answer"]
        # return data

    except requests.exceptions.ConnectionError:

        return (
            "⚠️ Unable to connect to the FinanceAI "
            "backend. Make sure FastAPI is running."
        )

    except requests.exceptions.Timeout:

        return (
            "⚠️ The backend took too long to respond."
        )

    except requests.exceptions.RequestException as e:

        return f"⚠️ Backend error: {str(e)}"


# ------------------------------------
# Chat input
# ------------------------------------

prompt = st.chat_input(
    "Ask FinanceAI anything..."
)

if prompt:

    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    # Show spinner while backend processes
    with st.spinner("FinanceAI is thinking..."):

        ai_response = call_fastapi(prompt)

    # Add backend response
    st.session_state.messages.append({
        "role": "assistant",
        "content": ai_response
    })

    st.rerun()


# ------------------------------------
# Footer
# ------------------------------------

st.markdown("""
<div class="disclaimer">
FinanceAI provides informational analysis only.
It is not financial, investment, tax, or legal advice.
</div>
""", unsafe_allow_html=True)
