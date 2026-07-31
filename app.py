import streamlit as st

st.set_page_config(
    page_title="VoiceBridge-PST",
    page_icon="🎙️",
    layout="wide"
)

TASK_BANK = {
    "Pedagogy of Mathematics": [
        {
            "id": "MATH-01",
            "category": "Misconception Diagnosis",
            "prompt": "A Class VI student says that a larger denominator means a larger fraction. How will you respond as a teacher?"
        },
        {
            "id": "MATH-02",
            "category": "Error Analysis",
            "prompt": "A student solves 3x + 5 = 20 as 3x = 25. How will you identify and address this error?"
        },
        {
            "id": "MATH-03",
            "category": "Concept Explanation",
            "prompt": "How would you explain the difference between area and perimeter to Class VII students?"
        }
    ],

    "Pedagogy of Science": [
        {
            "id": "SCI-01",
            "category": "Misconception Diagnosis",
            "prompt": "A Class VII student says that heat and temperature are the same. How will you respond as a teacher?"
        },
        {
            "id": "SCI-02",
            "category": "Concept Explanation",
            "prompt": "How would you introduce evaporation through a familiar daily-life situation?"
        },
        {
            "id": "SCI-03",
            "category": "Short Activity Design",
            "prompt": "Suggest a short classroom activity to demonstrate that air occupies space."
        }
    ],

    "Pedagogy of Social Science": [
        {
            "id": "SOC-01",
            "category": "Misconception Diagnosis",
            "prompt": "A Class VIII student says that democracy only means voting. How will you respond as a teacher?"
        },
        {
            "id": "SOC-02",
            "category": "Concept Explanation",
            "prompt": "How would you explain equality and equity through a classroom or community example?"
        },
        {
            "id": "SOC-03",
            "category": "Classroom Engagement",
            "prompt": "Students find history dates boring and disconnected from life. What teaching strategy will you use?"
        }
    ],

    "Pedagogy of English": [
        {
            "id": "ENG-01",
            "category": "Learner Support",
            "prompt": "A student can read a passage aloud but cannot infer its meaning. How will you support the learner?"
        },
        {
            "id": "ENG-02",
            "category": "Classroom Engagement",
            "prompt": "Students hesitate to speak in English during class. What will you do?"
        },
        {
            "id": "ENG-03",
            "category": "Assessment Decision",
            "prompt": "After teaching a poem, how would you assess comprehension beyond memorisation?"
        }
    ],

    "Pedagogy of Hindi": [
        {
            "id": "HIN-01",
            "category": "Misconception Diagnosis",
            "prompt": "A student memorises a poem but cannot explain its meaning. How will you respond?"
        },
        {
            "id": "HIN-02",
            "category": "Concept Explanation",
            "prompt": "How would you introduce idioms through daily-life situations?"
        },
        {
            "id": "HIN-03",
            "category": "Classroom Engagement",
            "prompt": "Students are not interested in reading a Hindi passage aloud. What will you do?"
        }
    ],

    "Pedagogy of Commerce": [
        {
            "id": "COM-01",
            "category": "Misconception Diagnosis",
            "prompt": "A student says that sales and profit are the same. How will you respond?"
        },
        {
            "id": "COM-02",
            "category": "Concept Explanation",
            "prompt": "How would you explain assets and liabilities using examples from daily life?"
        },
        {
            "id": "COM-03",
            "category": "Classroom Engagement",
            "prompt": "Students find accounting rules mechanical and boring. What teaching strategy will you use?"
        }
    ],

    "Pedagogy of Computer Science": [
        {
            "id": "CS-01",
            "category": "Misconception Diagnosis",
            "prompt": "A student says that the internet and the web are the same. How will you respond?"
        },
        {
            "id": "CS-02",
            "category": "Concept Explanation",
            "prompt": "How would you explain an algorithm using a daily-life example?"
        },
        {
            "id": "CS-03",
            "category": "Inclusive Adaptation",
            "prompt": "How would you support a learner who has limited access to a computer outside the classroom?"
        }
    ]
}

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
    st.write("Select your pedagogy subject and a pedagogical task.")

    selected_subject = st.selectbox(
        "Pedagogy Subject",
        list(TASK_BANK.keys()),
        key="selected_subject"
    )

    subject_tasks = TASK_BANK[selected_subject]

    task_labels = [
        f'{task["id"]} — {task["category"]}'
        for task in subject_tasks
    ]

    selected_task_label = st.selectbox(
        "Task",
        task_labels,
        key="selected_task"
    )

    selected_task_index = task_labels.index(selected_task_label)
    selected_task = subject_tasks[selected_task_index]

    st.markdown("### Pedagogical Prompt")
    st.info(selected_task["prompt"])

    col1, col2 = st.columns(2)

    with col1:
        st.text_input(
            "Task ID",
            value=selected_task["id"],
            disabled=True
        )

    with col2:
        st.text_input(
            "Task Category",
            value=selected_task["category"],
            disabled=True
        )

    st.success(
        "Subject and task selection are working. "
        "Participant details and response submission will be added next."
    )

elif page == "Review Responses":
    st.title("Review Responses")
    st.info(
        "Response review will be added after the submission form is connected."
    )

elif page == "Score Responses":
    st.title("Score Responses")
    st.info(
        "Rubric scoring will be added after response submission is working."
    )

elif page == "Diagnostic Profile":
    st.title("Diagnostic Profile")
    st.info(
        "Individual diagnostic profiles will be added after scoring is working."
    )

elif page == "Task Analytics":
    st.title("Task Analytics")
    st.info(
        "Task-level analytics will be added after scoring data are available."
    )

elif page == "Download Data":
    st.title("Download Data")
    st.info(
        "Data download will be added after submissions are stored."
    )