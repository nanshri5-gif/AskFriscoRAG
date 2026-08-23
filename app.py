import streamlit as st
import requests

from datetime import datetime
from zoneinfo import ZoneInfo

from langchain_core.messages import HumanMessage, AIMessage
from rag import ask_frisco


# ---------------------------------------------------
# Page configuration
# ---------------------------------------------------

st.set_page_config(
    page_title="AskFrisco",
    page_icon="🏙️",
    layout="centered",
)


# ---------------------------------------------------
# Weather
# ---------------------------------------------------

@st.cache_data(ttl=600)
def get_frisco_weather():

    # Approximate Frisco, TX coordinates
    latitude = 33.1507
    longitude = -96.8236

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": [
            "temperature_2m",
            "apparent_temperature",
            "weather_code"
        ],
        "temperature_unit": "fahrenheit",
        "timezone": "America/Chicago",
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        return data["current"]

    except requests.RequestException:
        return None


def weather_description(code):

    if code == 0:
        return "Clear"

    elif code in [1, 2]:
        return "Partly cloudy"

    elif code == 3:
        return "Cloudy"

    elif code in [45, 48]:
        return "Foggy"

    elif code in [51, 53, 55, 56, 57]:
        return "Drizzle"

    elif code in [61, 63, 65, 66, 67]:
        return "Rain"

    elif code in [71, 73, 75, 77]:
        return "Snow"

    elif code in [80, 81, 82]:
        return "Rain showers"

    elif code in [95, 96, 99]:
        return "Thunderstorms"

    return "Weather unavailable"


# ---------------------------------------------------
# Header
# ---------------------------------------------------

st.title("🏙️ AskFrisco")

st.subheader("Your Frisco City Information Assistant")

st.write(
    """
Frisco is a growing North Texas community with city services,
parks, recreation facilities, community events, and resident
resources.

AskFrisco helps you quickly find information from a curated
collection of Frisco city documents.
"""
)


# ---------------------------------------------------
# Frisco Today
# ---------------------------------------------------

frisco_now = datetime.now(
    ZoneInfo("America/Chicago")
)

weather = get_frisco_weather()

st.markdown("### Frisco Today")

date_col, time_col, weather_col = st.columns(3)

with date_col:

    st.metric(
        label="📅 Date",
        value=frisco_now.strftime("%b %d, %Y")
    )


with time_col:

    st.metric(
        label="🕐 Local Time",
        value=frisco_now.strftime("%I:%M %p")
    )


with weather_col:

    if weather:

        temperature = round(
            weather["temperature_2m"]
        )

        condition = weather_description(
            weather["weather_code"]
        )

        st.metric(
            label="🌤️ Weather",
            value=f"{temperature}°F",
            delta=condition,
            delta_color="off"
        )

    else:

        st.metric(
            label="🌤️ Weather",
            value="Unavailable"
        )


# ---------------------------------------------------
# Knowledge-base notice
# ---------------------------------------------------

st.info(
    'AskFrisco answers city-information questions only from '
    'its curated knowledge base. If the information is not '
    'available, it will say: '
    '"I don\'t have that info available."'
)


# ---------------------------------------------------
# Initialize session state
# ---------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []


# ---------------------------------------------------
# Suggested questions
# ---------------------------------------------------

st.markdown("### Try asking")

col1, col2 = st.columns(2)

with col1:

    q1 = st.button(
        "🏛️ When does City Council meet?",
        use_container_width=True,
    )

    q2 = st.button(
        "🛹 What time does the skate park close?",
        use_container_width=True,
    )


with col2:

    q3 = st.button(
        "🗑️ When should I put out my trash cart?",
        use_container_width=True,
    )

    q4 = st.button(
        "🎪 Do I need a special-event permit?",
        use_container_width=True,
    )


# ---------------------------------------------------
# Display conversation history
# ---------------------------------------------------

st.markdown("---")

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# ---------------------------------------------------
# Chat input
# ---------------------------------------------------

typed_question = st.chat_input(
    "Ask a question about Frisco..."
)


# ---------------------------------------------------
# Determine question
# ---------------------------------------------------

question = None

if q1:

    question = (
        "When does the Frisco City Council meet?"
    )

elif q2:

    question = (
        "What time does the Frisco Skate Park close?"
    )

elif q3:

    question = (
        "When should I put out my trash cart?"
    )

elif q4:

    question = (
        "Do I need a special-event permit?"
    )

elif typed_question:

    question = typed_question


# ---------------------------------------------------
# Process question
# ---------------------------------------------------

if question:

    with st.chat_message("user"):

        st.markdown(question)


    # Build conversation memory
    chat_history = []

    for message in st.session_state.messages:

        if message["role"] == "user":

            chat_history.append(
                HumanMessage(
                    content=message["content"]
                )
            )

        elif message["role"] == "assistant":

            chat_history.append(
                AIMessage(
                    content=message["content"]
                )
            )


    # Run RAG
    with st.spinner(
        "Searching the AskFrisco knowledge base..."
    ):

        answer = ask_frisco(
            question,
            chat_history
        )


    # Display answer
    with st.chat_message("assistant"):

        st.markdown(answer)


    # Save conversation
    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )