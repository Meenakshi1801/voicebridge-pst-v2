import streamlit as st

st.set_page_config(
    page_title="VoiceBridge-PST",
    page_icon="🎙️",
    layout="wide"
)

st.sidebar.title("🎙️ VoiceBridge-PST")
st.sidebar.caption("Activity and Analytics Platform")

page = st.sidebar.radio(
    "Navigation",
    [
        "Home",
        "Activity Submission",
        "Review Responses",
        "Score Responses",
        "Diagnostic Profile",
        "Task Analytics",
        "Download Data"
    ],
    key="main_navigation"
)

if page == "Home":
    st.title("🎙️ VoiceBridge-PST Dashboard")
    st.subheader(
        "Voice-First Micro-Pedagogical Reasoning Activity and Analytics Platform"
    )

    st.markdown(
        """
        <div style="line-height:1.3;">
            <span style="font-size:14px; color:#666;">
                Conceptualized and Developed by
            </span><br>
            <b>Dr. Meenakshi Dwivedi</b><br>
            Assistant Professor<br>
            Department of Education / School of Education<br>
            Mahatma Jyotiba Phule Rohilkhand University,
            Bareilly, Uttar Pradesh, India
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    st.header("Purpose")
    st.write(
        "VoiceBridge-PST is a voice-first activity and analytics platform "
        "for assessing micro-pedagogical reasoning among pre-service teachers."
    )

elif page == "Activity Submission":
    st.title("Activity Submission")
    st.success("The Activity Submission page is working.")

elif page == "Review Responses":
    st.title("Review Responses")
    st.success("The Review Responses page is working.")

elif page == "Score Responses":
    st.title("Score Responses")
    st.success("The Score Responses page is working.")

elif page == "Diagnostic Profile":
    st.title("Diagnostic Profile")
    st.success("The Diagnostic Profile page is working.")

elif page == "Task Analytics":
    st.title("Task Analytics")
    st.success("The Task Analytics page is working.")

elif page == "Download Data":
    st.title("Download Data")
    st.success("The Download Data page is working.")
