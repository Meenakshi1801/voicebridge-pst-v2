from __future__ import annotations

import csv
from datetime import datetime
from io import StringIO
from typing import Any

import streamlit as st


st.set_page_config(
    page_title="VoiceBridge-PST",
    page_icon="🎙️",
    layout="wide",
)


# =======================================================
# Subject-wise task bank
# =======================================================

TASK_BANK: dict[str, list[dict[str, str]]] = {
    "Pedagogy of Mathematics": [
        {
            "id": "MATH-01",
            "category": "Misconception Diagnosis",
            "prompt": (
                "A Class VI student says that a larger denominator means a "
                "larger fraction. How will you respond as a teacher?"
            ),
        },
        {
            "id": "MATH-02",
            "category": "Error Analysis",
            "prompt": (
                "A student solves 3x + 5 = 20 as 3x = 25. How will you "
                "identify and address this error?"
            ),
        },
        {
            "id": "MATH-03",
            "category": "Concept Explanation",
            "prompt": (
                "How would you explain the difference between area and "
                "perimeter to Class VII students?"
            ),
        },
    ],

    "Pedagogy of Science": [
        {
            "id": "SCI-01",
            "category": "Misconception Diagnosis",
            "prompt": (
                "A Class VII student says that heat and temperature are the "
                "same. How will you respond as a teacher?"
            ),
        },
        {
            "id": "SCI-02",
            "category": "Concept Explanation",
            "prompt": (
                "How would you introduce evaporation through a familiar "
                "daily-life situation?"
            ),
        },
        {
            "id": "SCI-03",
            "category": "Short Activity Design",
            "prompt": (
                "Suggest a short classroom activity to demonstrate that air "
                "occupies space."
            ),
        },
    ],

    "Pedagogy of Social Science": [
        {
            "id": "SOC-01",
            "category": "Misconception Diagnosis",
            "prompt": (
                "A Class VIII student says that democracy only means voting. "
                "How will you respond as a teacher?"
            ),
        },
        {
            "id": "SOC-02",
            "category": "Concept Explanation",
            "prompt": (
                "How would you explain equality and equity through a "
                "classroom or community example?"
            ),
        },
        {
            "id": "SOC-03",
            "category": "Classroom Engagement",
            "prompt": (
                "Students find history dates boring and disconnected from "
                "life. What teaching strategy will you use?"
            ),
        },
    ],

    "Pedagogy of English": [
        {
            "id": "ENG-01",
            "category": "Learner Support",
            "prompt": (
                "A student can read a passage aloud but cannot infer its "
                "meaning. How will you support the learner?"
            ),
        },
        {
            "id": "ENG-02",
            "category": "Classroom Engagement",
            "prompt": (
                "Students hesitate to speak in English during class. "
                "What will you do?"
            ),
        },
        {
            "id": "ENG-03",
            "category": "Assessment Decision",
            "prompt": (
                "After teaching a poem, how would you assess comprehension "
                "beyond memorisation?"
            ),
        },
    ],

    "Pedagogy of Hindi": [
        {
            "id": "HIN-01",
            "category": "Misconception Diagnosis",
            "prompt": (
                "A student memorises a poem but cannot explain its meaning. "
                "How will you respond?"
            ),
        },
        {
            "id": "HIN-02",
            "category": "Concept Explanation",
            "prompt": (
                "How would you introduce idioms through daily-life situations?"
            ),
        },
        {
            "id": "HIN-03",
            "category": "Classroom Engagement",
            "prompt": (
                "Students are not interested in reading a Hindi passage aloud. "
                "What will you do?"
            ),
        },
    ],

    "Pedagogy of Commerce": [
        {
            "id": "COM-01",
            "category": "Misconception Diagnosis",
            "prompt": (
                "A student says that sales and profit are the same. "
                "How will you respond?"
            ),
        },
        {
            "id": "COM-02",
            "category": "Concept Explanation",
            "prompt": (
                "How would you explain assets and liabilities using examples "
                "from daily life?"
            ),
        },
        {
            "id": "COM-03",
            "category": "Classroom Engagement",
            "prompt": (
                "Students find accounting rules mechanical and boring. "
                "What teaching strategy will you use?"
            ),
        },
    ],

    "Pedagogy of Computer Science": [
        {
            "id": "CS-01",
            "category": "Misconception Diagnosis",
            "prompt": (
                "A student says that the internet and the web are the same. "
                "How will you respond?"
            ),
        },
        {
            "id": "CS-02",
            "category": "Concept Explanation",
            "prompt": (
                "How would you explain an algorithm using a daily-life example?"
            ),
        },
        {
            "id": "CS-03",
            "category": "Inclusive Adaptation",
            "prompt": (
                "How would you support a learner who has limited access to "
                "a computer outside the classroom?"
            ),
        },
    ],
}


# =======================================================
# Session storage
# =======================================================

if "submissions" not in st.session_state:
    st.session_state.submissions = []


# =======================================================
# Helper functions
# =======================================================

def make_reference(student_id: str, task_id: str) -> str:
    safe_id = "".join(
        character
        for character in student_id.upper()
        if character.isalnum()
    )

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    return f"{safe_id}-{task_id}-{timestamp}"


def submissions_to_csv(
    submissions: list[dict[str, Any]]
) -> bytes:

    output = StringIO()

    fields = [
        "submission_reference",
        "student_id",
        "name",
        "semester",
        "pedagogy_subject",
        "task_id",
        "task_category",
        "prompt",
        "written_response",
        "reflection_issue",
        "reflection_strategy",
        "submission_time",
        "audio_file_name",
        "audio_mime_type",
    ]

    writer = csv.DictWriter(
        output,
        fieldnames=fields,
    )

    writer.writeheader()

    for submission in submissions:
        writer.writerow(
            {
                field: submission.get(field, "")
                for field in fields
            }
        )

    return output.getvalue().encode("utf-8-sig")


# =======================================================
# Sidebar navigation
# =======================================================

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
        "Download Data",
    ],
    key="main_navigation",
)

st.sidebar.divider()

st.sidebar.metric(
    "Current-session submissions",
    len(st.session_state.submissions),
)


# =======================================================
# Home page
# =======================================================

if page == "Home":

    st.title("🎙️ VoiceBridge-PST Dashboard")

    st.subheader(
        "Voice-First Micro-Pedagogical Reasoning "
        "Activity and Analytics Platform"
    )

    st.markdown(
        """
        <div style="line-height:1.3; margin-top:0.25rem;">
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
        unsafe_allow_html=True,
    )

    st.divider()

    st.header("Purpose")

    st.write(
        "VoiceBridge-PST is a voice-first activity and analytics "
        "platform for assessing micro-pedagogical reasoning among "
        "pre-service teachers."
    )

    st.header("Activity Flow")

    st.write(
        "Pedagogical prompt → Voice reasoning → Written pedagogical "
        "response → Reflective response → Teacher-educator review"
    )

    st.header("Pedagogy Subjects")

    for subject in TASK_BANK:
        st.write(f"• {subject}")


# =======================================================
# Activity submission
# =======================================================

elif page == "Activity Submission":

    st.title("Activity Submission")

    st.write(
        "Select your pedagogy subject and task. Then record your "
        "voice reasoning and complete the written and reflective "
        "responses."
    )

    selected_subject = st.selectbox(
        "Pedagogy Subject",
        list(TASK_BANK.keys()),
        key="selected_subject",
    )

    subject_tasks = TASK_BANK[selected_subject]

    task_labels = [
        f'{task["id"]} — {task["category"]}'
        for task in subject_tasks
    ]

    selected_task_label = st.selectbox(
        "Task",
        task_labels,
        key="selected_task",
    )

    selected_task_index = task_labels.index(
        selected_task_label
    )

    selected_task = subject_tasks[selected_task_index]

    st.markdown("### Pedagogical Prompt")

    st.info(
        selected_task["prompt"]
    )

    task_col1, task_col2 = st.columns(2)

    with task_col1:
        st.text_input(
            "Task ID",
            value=selected_task["id"],
            disabled=True,
        )

    with task_col2:
        st.text_input(
            "Task Category",
            value=selected_task["category"],
            disabled=True,
        )

    st.divider()

    # ---------------------------------------------------
    # Stage 1: Voice reasoning
    # ---------------------------------------------------

    st.markdown("## Stage 1: Voice Reasoning")

    st.write(
        "Think aloud and explain how you understand the pedagogical "
        "situation and how you would respond as a teacher."
    )

    st.caption(
        "Suggested duration: 2–3 minutes. Allow microphone access "
        "when requested."
    )

    audio_response = st.audio_input(
        "Record your voice response",
        key=(
            f'audio_{selected_subject}_'
            f'{selected_task["id"]}'
        ),
    )

    if audio_response is not None:

        st.success(
            "Voice response recorded successfully."
        )

        st.audio(
            audio_response
        )

    st.divider()

    # ---------------------------------------------------
    # Participant and written response form
    # ---------------------------------------------------

    with st.form(
        "participant_response_form",
        clear_on_submit=False,
    ):

        st.markdown("## Participant Details")

        participant_col1, participant_col2 = st.columns(2)

        with participant_col1:

            student_id = st.text_input(
                "Student ID / Participant Code",
                placeholder="Example: PST001",
            )

            participant_name = st.text_input(
                "Name",
                placeholder="Enter your name",
            )

        with participant_col2:

            semester = st.selectbox(
                "B.Ed. Semester",
                [
                    "Semester I",
                    "Semester II",
                    "Semester III",
                    "Semester IV",
                ],
            )

            st.text_input(
                "Selected Pedagogy Subject",
                value=selected_subject,
                disabled=True,
            )

        # ------------------------------------------------
        # Stage 2: Written response
        # ------------------------------------------------

        st.markdown(
            "## Stage 2: Written Pedagogical Response"
        )

        written_response = st.text_area(
            "Explain how you would respond to the pedagogical situation.",
            placeholder=(
                "Describe what you would say or do as a teacher "
                "and explain the reasoning behind your response."
            ),
            height=180,
        )

        st.caption(
            "Suggested length: approximately 150–200 words."
        )

        # ------------------------------------------------
        # Stage 3: Reflection
        # ------------------------------------------------

        st.markdown(
            "## Stage 3: Reflective Response"
        )

        reflection_issue = st.text_area(
            (
                "What learner difficulty, misconception, error, "
                "or pedagogical issue did you identify?"
            ),
            height=120,
        )

        reflection_strategy = st.text_area(
            (
                "What example, activity, explanation, assessment "
                "method, or teaching strategy would you use?"
            ),
            height=120,
        )

        declaration = st.checkbox(
            (
                "I confirm that the voice and written responses "
                "are my own work."
            )
        )

        submit_response = st.form_submit_button(
            "Submit Activity",
            type="primary",
        )

    # ---------------------------------------------------
    # Validate and save response
    # ---------------------------------------------------

    if submit_response:

        errors: list[str] = []

        if not student_id.strip():
            errors.append(
                "Enter your Student ID / Participant Code."
            )

        if not participant_name.strip():
            errors.append(
                "Enter your name."
            )

        if audio_response is None:
            errors.append(
                "Record your voice response."
            )

        if not written_response.strip():
            errors.append(
                "Enter your written pedagogical response."
            )

        if not reflection_issue.strip():
            errors.append(
                "Complete the first reflection question."
            )

        if not reflection_strategy.strip():
            errors.append(
                "Complete the second reflection question."
            )

        if not declaration:
            errors.append(
                "Confirm the originality declaration."
            )

        if errors:

            st.error(
                "Please complete the following before submitting:"
            )

            for error in errors:
                st.write(f"• {error}")

        else:

            submission_reference = make_reference(
                student_id.strip(),
                selected_task["id"],
            )

            audio_file_name = getattr(
                audio_response,
                "name",
                f"{submission_reference}.wav",
            )

            audio_mime_type = getattr(
                audio_response,
                "type",
                "audio/wav",
            )

            submission: dict[str, Any] = {
                "submission_reference": submission_reference,
                "student_id": student_id.strip(),
                "name": participant_name.strip(),
                "semester": semester,
                "pedagogy_subject": selected_subject,
                "task_id": selected_task["id"],
                "task_category": selected_task["category"],
                "prompt": selected_task["prompt"],
                "audio_bytes": audio_response.getvalue(),
                "audio_file_name": audio_file_name,
                "audio_mime_type": audio_mime_type,
                "written_response": written_response.strip(),
                "reflection_issue": reflection_issue.strip(),
                "reflection_strategy": reflection_strategy.strip(),
                "submission_time": datetime.now().strftime(
                    "%d-%m-%Y %I:%M %p"
                ),
            }

            st.session_state.submissions.append(
                submission
            )

            st.success(
                "Your activity has been submitted successfully."
            )

            st.info(
                f"Submission reference: {submission_reference}"
            )


# =======================================================
# Review responses
# =======================================================

elif page == "Review Responses":

    st.title("Review Responses")

    if not st.session_state.submissions:

        st.warning(
            "No responses have been submitted in the current session."
        )

    else:

        st.write(
            "Total submissions in this session: "
            f"{len(st.session_state.submissions)}"
        )

        response_labels = [
            (
                f'{submission["student_id"]} — '
                f'{submission["task_id"]} — '
                f'{submission["name"]}'
            )
            for submission in st.session_state.submissions
        ]

        selected_response_label = st.selectbox(
            "Select a response",
            response_labels,
        )

        response_index = response_labels.index(
            selected_response_label
        )

        response = st.session_state.submissions[
            response_index
        ]

        st.divider()

        detail_col1, detail_col2, detail_col3 = st.columns(3)

        detail_col1.metric(
            "Participant Code",
            response["student_id"],
        )

        detail_col2.metric(
            "Task",
            response["task_id"],
        )

        detail_col3.metric(
            "Semester",
            response["semester"],
        )

        st.markdown(
            "### Participant Information"
        )

        st.write(
            f'**Name:** {response["name"]}'
        )

        st.write(
            f'**Pedagogy Subject:** '
            f'{response["pedagogy_subject"]}'
        )

        st.write(
            f'**Task Category:** '
            f'{response["task_category"]}'
        )

        st.write(
            f'**Submission Time:** '
            f'{response["submission_time"]}'
        )

        st.write(
            f'**Reference:** '
            f'{response["submission_reference"]}'
        )

        st.markdown(
            "### Pedagogical Prompt"
        )

        st.info(
            response["prompt"]
        )

        st.markdown(
            "### Voice Reasoning"
        )

        st.audio(
            response["audio_bytes"],
            format=response.get(
                "audio_mime_type",
                "audio/wav",
            ),
        )

        st.markdown(
            "### Written Pedagogical Response"
        )

        st.write(
            response["written_response"]
        )

        st.markdown(
            "### Reflection: Identified Issue"
        )

        st.write(
            response["reflection_issue"]
        )

        st.markdown(
            "### Reflection: Proposed Strategy"
        )

        st.write(
            response["reflection_strategy"]
        )


# =======================================================
# Score responses
# =======================================================

elif page == "Score Responses":

    st.title("Score Responses")

    if not st.session_state.submissions:

        st.warning(
            "No responses are available for scoring "
            "in the current session."
        )

    else:

        st.info(
            "Rubric-based scoring will be added after the "
            "participant submission and response-review workflow "
            "has been tested."
        )


# =======================================================
# Diagnostic profile
# =======================================================

elif page == "Diagnostic Profile":

    st.title("Diagnostic Profile")

    st.info(
        "Individual diagnostic profiles will be added after "
        "rubric scoring is working."
    )


# =======================================================
# Task analytics
# =======================================================

elif page == "Task Analytics":

    st.title("Task Analytics")

    submission_count = len(
        st.session_state.submissions
    )

    participant_count = len(
        {
            submission["student_id"]
            for submission in st.session_state.submissions
        }
    )

    subject_count = len(
        {
            submission["pedagogy_subject"]
            for submission in st.session_state.submissions
        }
    )

    metric_col1, metric_col2, metric_col3 = st.columns(3)

    metric_col1.metric(
        "Submissions",
        submission_count,
    )

    metric_col2.metric(
        "Participants",
        participant_count,
    )

    metric_col3.metric(
        "Subjects represented",
        subject_count,
    )

    if submission_count == 0:

        st.warning(
            "No submission data are available in the current session."
        )

    else:

        st.markdown(
            "### Submission Summary"
        )

        for submission in st.session_state.submissions:

            st.write(
                f'• {submission["student_id"]} | '
                f'{submission["pedagogy_subject"]} | '
                f'{submission["task_id"]}'
            )


# =======================================================
# Download data
# =======================================================

elif page == "Download Data":

    st.title("Download Data")

    if not st.session_state.submissions:

        st.warning(
            "No responses are available for download "
            "in the current session."
        )

    else:

        csv_data = submissions_to_csv(
            st.session_state.submissions
        )

        st.download_button(
            "Download submission data as CSV",
            data=csv_data,
            file_name="VoiceBridge_PST_Submissions.csv",
            mime="text/csv",
        )

        st.caption(
            "The CSV contains participant details, task information, "
            "written responses, reflections, and audio-file metadata. "
            "The audio recordings can be reviewed inside the app."
        )