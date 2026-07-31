
from __future__ import annotations

import csv
from datetime import datetime
from io import StringIO
from typing import Any

import streamlit as st


st.set_page_config(
    page_title="VoiceBridge-PST",
    page_icon="ðŸŽ™ï¸",
    layout="wide",
)


# =======================================================
# Assessment rubric
# =======================================================

RUBRIC: dict[str, str] = {
    "conceptual_clarity": "Conceptual Clarity",
    "pedagogical_reasoning": "Pedagogical Reasoning",
    "learner_centred_explanation": "Learner-Centred Explanation",
    "misconception_diagnosis": "Misconception Diagnosis",
    "use_of_example_strategy": "Use of Example / Teaching Strategy",
    "reflective_thinking": "Reflective Thinking",
    "voice_written_alignment": "Voice-Written Alignment",
}

RUBRIC_MAXIMUM = len(RUBRIC) * 5

IMPROVEMENT_GUIDANCE: dict[str, str] = {
    "conceptual_clarity": (
        "Clarify the central concept and distinguish it from related ideas."
    ),
    "pedagogical_reasoning": (
        "Explain more clearly why the proposed teaching response is appropriate."
    ),
    "learner_centred_explanation": (
        "Connect the response more directly with the learner's level, needs, and context."
    ),
    "misconception_diagnosis": (
        "Identify the exact misconception, error pattern, or learning difficulty more precisely."
    ),
    "use_of_example_strategy": (
        "Use a more concrete example, analogy, activity, question, or assessment strategy."
    ),
    "reflective_thinking": (
        "Reflect more deeply on possible limitations, alternatives, and improvements."
    ),
    "voice_written_alignment": (
        "Ensure that the written response accurately represents and develops the oral reasoning."
    ),
}


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

if "activity_nonce" not in st.session_state:
    st.session_state.activity_nonce = 0


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


def response_label(submission: dict[str, Any]) -> str:
    return (
        f'{submission["student_id"]} â€” {submission["task_id"]} â€” '
        f'{submission["name"]} â€” {submission["submission_reference"][-6:]}'
    )


def score_total(submission: dict[str, Any]) -> int:
    scores = submission.get("scores") or {}
    return sum(int(scores.get(key, 0)) for key in RUBRIC)


def score_percentage(submission: dict[str, Any]) -> float:
    if not submission.get("scores"):
        return 0.0
    return (score_total(submission) / RUBRIC_MAXIMUM) * 100


def suggested_feedback(scores: dict[str, int]) -> str:
    if not scores:
        return "No rubric scores are available."

    strongest_key = max(scores, key=scores.get)
    weakest_key = min(scores, key=scores.get)

    return (
        f"Strongest area: {RUBRIC[strongest_key]}. "
        f"Priority for improvement: {RUBRIC[weakest_key]}. "
        f"Suggested action: {IMPROVEMENT_GUIDANCE[weakest_key]}"
    )


def submissions_to_csv(
    submissions: list[dict[str, Any]],
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
        *RUBRIC.keys(),
        "total_score",
        "maximum_score",
        "percentage",
        "teacher_feedback",
        "scored_time",
    ]

    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()

    for submission in submissions:
        scores = submission.get("scores") or {}
        row = {
            "submission_reference": submission.get("submission_reference", ""),
            "student_id": submission.get("student_id", ""),
            "name": submission.get("name", ""),
            "semester": submission.get("semester", ""),
            "pedagogy_subject": submission.get("pedagogy_subject", ""),
            "task_id": submission.get("task_id", ""),
            "task_category": submission.get("task_category", ""),
            "prompt": submission.get("prompt", ""),
            "written_response": submission.get("written_response", ""),
            "reflection_issue": submission.get("reflection_issue", ""),
            "reflection_strategy": submission.get("reflection_strategy", ""),
            "submission_time": submission.get("submission_time", ""),
            "audio_file_name": submission.get("audio_file_name", ""),
            "audio_mime_type": submission.get("audio_mime_type", ""),
            "total_score": score_total(submission) if scores else "",
            "maximum_score": RUBRIC_MAXIMUM if scores else "",
            "percentage": round(score_percentage(submission), 2) if scores else "",
            "teacher_feedback": submission.get("teacher_feedback", ""),
            "scored_time": submission.get("scored_time", ""),
        }

        for key in RUBRIC:
            row[key] = scores.get(key, "")

        writer.writerow(row)

    return output.getvalue().encode("utf-8-sig")


def aggregate_rows(
    submissions: list[dict[str, Any]],
    group_field: str,
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, float]] = {}

    for submission in submissions:
        group_name = str(submission.get(group_field, "Not specified"))
        if group_name not in grouped:
            grouped[group_name] = {
                "submissions": 0,
                "scored": 0,
                "percentage_sum": 0.0,
            }

        grouped[group_name]["submissions"] += 1

        if submission.get("scores"):
            grouped[group_name]["scored"] += 1
            grouped[group_name]["percentage_sum"] += score_percentage(submission)

    rows = []

    for group_name, values in grouped.items():
        scored = int(values["scored"])
        average = values["percentage_sum"] / scored if scored else 0.0

        rows.append(
            {
                group_field.replace("_", " ").title(): group_name,
                "Submissions": int(values["submissions"]),
                "Scored": scored,
                "Average Percentage": round(average, 2) if scored else "",
            }
        )

    return sorted(
        rows,
        key=lambda row: str(
            row[group_field.replace("_", " ").title()]
        ),
    )


def display_response_material(submission: dict[str, Any]) -> None:
    st.markdown("### Pedagogical Prompt")
    st.info(submission["prompt"])

    st.markdown("### Voice Reasoning")
    st.audio(
        submission["audio_bytes"],
        format=submission.get("audio_mime_type", "audio/wav"),
    )

    st.download_button(
        "Download this audio recording",
        data=submission["audio_bytes"],
        file_name=submission.get(
            "audio_file_name",
            f'{submission["submission_reference"]}.wav',
        ),
        mime=submission.get("audio_mime_type", "audio/wav"),
        key=f'audio_download_{submission["submission_reference"]}',
    )

    st.markdown("### Written Pedagogical Response")
    st.write(submission["written_response"])

    st.markdown("### Reflection: Identified Issue")
    st.write(submission["reflection_issue"])

    st.markdown("### Reflection: Proposed Strategy")
    st.write(submission["reflection_strategy"])


# =======================================================
# Sidebar navigation
# =======================================================

st.sidebar.title("ðŸŽ™ï¸ VoiceBridge-PST")
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

st.sidebar.metric(
    "Scored responses",
    sum(
        1
        for submission in st.session_state.submissions
        if submission.get("scores")
    ),
)


# =======================================================
# Home page
# =======================================================

if page == "Home":
    st.title("ðŸŽ™ï¸ VoiceBridge-PST Dashboard")

    st.subheader(
        "Voice-First Micro-Pedagogical Reasoning "
        "Activity and Analytics Platform"
    )

    developer_html = (
        '<div style="line-height:1.35; margin-top:0.25rem;">'
        '<span style="font-size:14px; color:#666;">'
        'Conceptualized and Developed by'
        '</span><br>'
        '<b>Dr. Meenakshi Dwivedi</b><br>'
        'Assistant Professor<br>'
        'Department of Education / School of Education<br>'
        'Mahatma Jyotiba Phule Rohilkhand University<br>'
        'Bareilly, Uttar Pradesh, India'
        '</div>'
    )

    st.markdown(developer_html, unsafe_allow_html=True)
    st.divider()

    st.header("Purpose")
    st.write(
        "VoiceBridge-PST is a voice-first activity and analytics "
        "platform for assessing micro-pedagogical reasoning among "
        "pre-service teachers."
    )

    st.header("Activity Flow")
    st.write(
        "Pedagogical prompt â†’ Voice reasoning â†’ Written pedagogical "
        "response â†’ Reflective response â†’ Rubric scoring â†’ "
        "Diagnostic feedback"
    )

    st.header("Assessment Dimensions")
    for number, label in enumerate(RUBRIC.values(), start=1):
        st.write(f"{number}. {label}")

    st.header("Pedagogy Subjects")
    for subject in TASK_BANK:
        st.write(f"â€¢ {subject}")


# =======================================================
# Activity submission
# =======================================================

elif page == "Activity Submission":
    st.title("Activity Submission")

    if "submission_message" in st.session_state:
        st.success(st.session_state.pop("submission_message"))
        reference = st.session_state.pop("submission_reference", "")
        if reference:
            st.info(f"Submission reference: {reference}")

    st.write(
        "Select your pedagogy subject and task. Then record your "
        "voice reasoning and complete the written and reflective responses."
    )

    nonce = st.session_state.activity_nonce

    selected_subject = st.selectbox(
        "Pedagogy Subject",
        list(TASK_BANK.keys()),
        key=f"selected_subject_{nonce}",
    )

    subject_tasks = TASK_BANK[selected_subject]

    task_labels = [
        f'{task["id"]} â€” {task["category"]}'
        for task in subject_tasks
    ]

    selected_task_label = st.selectbox(
        "Task",
        task_labels,
        key=f"selected_task_{nonce}",
    )

    selected_task = subject_tasks[task_labels.index(selected_task_label)]

    st.markdown("### Pedagogical Prompt")
    st.info(selected_task["prompt"])

    task_col1, task_col2 = st.columns(2)

    with task_col1:
        st.text_input(
            "Task ID",
            value=selected_task["id"],
            disabled=True,
            key=f"task_id_display_{nonce}",
        )

    with task_col2:
        st.text_input(
            "Task Category",
            value=selected_task["category"],
            disabled=True,
            key=f"task_category_display_{nonce}",
        )

    st.divider()
    st.markdown("## Stage 1: Voice Reasoning")

    st.write(
        "Think aloud and explain how you understand the pedagogical "
        "situation and how you would respond as a teacher."
    )

    st.caption(
        "Suggested duration: 2â€“3 minutes. "
        "Allow microphone access when requested."
    )

    audio_response = st.audio_input(
        "Record your voice response",
        key=f'audio_{nonce}_{selected_task["id"]}',
    )

    if audio_response is not None:
        st.success("Voice response recorded successfully.")
        st.audio(audio_response)

    st.divider()

    with st.form(
        f"participant_response_form_{nonce}",
        clear_on_submit=False,
    ):
        st.markdown("## Participant Details")

        participant_col1, participant_col2 = st.columns(2)

        with participant_col1:
            student_id = st.text_input(
                "Student ID / Participant Code",
                placeholder="Example: PST001",
                key=f"student_id_{nonce}",
            )

            participant_name = st.text_input(
                "Name",
                placeholder="Enter your name",
                key=f"participant_name_{nonce}",
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
                key=f"semester_{nonce}",
            )

            st.text_input(
                "Selected Pedagogy Subject",
                value=selected_subject,
                disabled=True,
                key=f"pedagogy_display_{nonce}",
            )

        st.markdown("## Stage 2: Written Pedagogical Response")

        written_response = st.text_area(
            "Explain how you would respond to the pedagogical situation.",
            placeholder=(
                "Describe what you would say or do as a teacher "
                "and explain the reasoning behind your response."
            ),
            height=180,
            key=f"written_response_{nonce}",
        )

        st.caption("Suggested length: approximately 150â€“200 words.")

        st.markdown("## Stage 3: Reflective Response")

        reflection_issue = st.text_area(
            (
                "What learner difficulty, misconception, error, "
                "or pedagogical issue did you identify?"
            ),
            height=120,
            key=f"reflection_issue_{nonce}",
        )

        reflection_strategy = st.text_area(
            (
                "What example, activity, explanation, assessment "
                "method, or teaching strategy would you use?"
            ),
            height=120,
            key=f"reflection_strategy_{nonce}",
        )

        declaration = st.checkbox(
            (
                "I confirm that the voice and written responses "
                "are my own work."
            ),
            key=f"declaration_{nonce}",
        )

        submit_response = st.form_submit_button(
            "Submit Activity",
            type="primary",
        )

    if submit_response:
        errors: list[str] = []

        if not student_id.strip():
            errors.append("Enter your Student ID / Participant Code.")

        if not participant_name.strip():
            errors.append("Enter your name.")

        if audio_response is None:
            errors.append("Record your voice response.")

        if not written_response.strip():
            errors.append("Enter your written pedagogical response.")

        if not reflection_issue.strip():
            errors.append("Complete the first reflection question.")

        if not reflection_strategy.strip():
            errors.append("Complete the second reflection question.")

        if not declaration:
            errors.append("Confirm the originality declaration.")

        if errors:
            st.error("Please complete the following before submitting:")
            for error in errors:
                st.write(f"â€¢ {error}")

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
                "scores": {},
                "teacher_feedback": "",
                "scored_time": "",
            }

            st.session_state.submissions.append(submission)
            st.session_state.submission_message = (
                "Your activity has been submitted successfully."
            )
            st.session_state.submission_reference = submission_reference
            st.session_state.activity_nonce += 1
            st.rerun()


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
            response_label(submission)
            for submission in st.session_state.submissions
        ]

        selected_label = st.selectbox(
            "Select a response",
            response_labels,
            key="review_response_selector",
        )

        response = st.session_state.submissions[
            response_labels.index(selected_label)
        ]

        st.divider()

        detail_col1, detail_col2, detail_col3 = st.columns(3)

        detail_col1.metric("Participant Code", response["student_id"])
        detail_col2.metric("Task", response["task_id"])
        detail_col3.metric("Semester", response["semester"])

        st.markdown("### Participant Information")
        st.write(f'**Name:** {response["name"]}')
        st.write(
            f'**Pedagogy Subject:** {response["pedagogy_subject"]}'
        )
        st.write(f'**Task Category:** {response["task_category"]}')
        st.write(f'**Submission Time:** {response["submission_time"]}')
        st.write(
            f'**Reference:** {response["submission_reference"]}'
        )

        display_response_material(response)

        if response.get("scores"):
            st.divider()
            st.markdown("### Rubric Result")

            result_col1, result_col2 = st.columns(2)
            result_col1.metric(
                "Total Score",
                f"{score_total(response)}/{RUBRIC_MAXIMUM}",
            )
            result_col2.metric(
                "Percentage",
                f"{score_percentage(response):.2f}%",
            )

            score_rows = [
                {
                    "Dimension": label,
                    "Score": response["scores"].get(key, ""),
                    "Maximum": 5,
                }
                for key, label in RUBRIC.items()
            ]
            st.dataframe(
                score_rows,
                use_container_width=True,
                hide_index=True,
            )

            if response.get("teacher_feedback"):
                st.markdown("### Teacher-Educator Feedback")
                st.info(response["teacher_feedback"])


# =======================================================
# Score responses
# =======================================================

elif page == "Score Responses":
    st.title("Score Responses")

    if "score_message" in st.session_state:
        st.success(st.session_state.pop("score_message"))

    if not st.session_state.submissions:
        st.warning(
            "No responses are available for scoring "
            "in the current session."
        )

    else:
        response_labels = [
            response_label(submission)
            for submission in st.session_state.submissions
        ]

        selected_label = st.selectbox(
            "Select a response to score",
            response_labels,
            key="score_response_selector",
        )

        response_index = response_labels.index(selected_label)
        response = st.session_state.submissions[response_index]

        status_text = (
            "Previously scored"
            if response.get("scores")
            else "Not yet scored"
        )

        heading_col1, heading_col2, heading_col3 = st.columns(3)
        heading_col1.metric("Participant", response["student_id"])
        heading_col2.metric("Task", response["task_id"])
        heading_col3.metric("Status", status_text)

        with st.expander(
            "Review the participant's complete response",
            expanded=True,
        ):
            display_response_material(response)

        st.divider()
        st.markdown("## Rubric Scoring")

        with st.expander("View scoring guide"):
            st.write("**1 â€” Very weak:** Criterion is largely absent.")
            st.write("**2 â€” Weak:** Criterion is present only minimally.")
            st.write("**3 â€” Moderate:** Criterion is adequately demonstrated.")
            st.write("**4 â€” Good:** Criterion is clearly and consistently demonstrated.")
            st.write("**5 â€” Excellent:** Criterion is demonstrated with depth and precision.")

        existing_scores = response.get("scores") or {}
        scores: dict[str, int] = {}

        left_column, right_column = st.columns(2)

        for index, (key, label) in enumerate(RUBRIC.items()):
            target_column = left_column if index % 2 == 0 else right_column
            current_value = int(existing_scores.get(key, 3))

            with target_column:
                scores[key] = st.slider(
                    label,
                    min_value=1,
                    max_value=5,
                    value=current_value,
                    step=1,
                    key=(
                        f'score_{response["submission_reference"]}_{key}'
                    ),
                )

        total = sum(scores.values())
        percentage = (total / RUBRIC_MAXIMUM) * 100

        result_col1, result_col2 = st.columns(2)
        result_col1.metric(
            "Current Total",
            f"{total}/{RUBRIC_MAXIMUM}",
        )
        result_col2.metric(
            "Current Percentage",
            f"{percentage:.2f}%",
        )

        st.markdown("### Suggested Diagnostic Feedback")
        automatic_feedback = suggested_feedback(scores)
        st.info(automatic_feedback)

        teacher_feedback = st.text_area(
            "Teacher-Educator Feedback",
            value=response.get("teacher_feedback", ""),
            placeholder=(
                "Write specific feedback for the pre-service teacher. "
                "You may adapt the suggested feedback above."
            ),
            height=140,
            key=(
                f'feedback_{response["submission_reference"]}'
            ),
        )

        if st.button(
            "Save Scores and Feedback",
            type="primary",
            key=(
                f'save_scores_{response["submission_reference"]}'
            ),
        ):
            response["scores"] = scores
            response["teacher_feedback"] = (
                teacher_feedback.strip()
                if teacher_feedback.strip()
                else automatic_feedback
            )
            response["scored_time"] = datetime.now().strftime(
                "%d-%m-%Y %I:%M %p"
            )

            st.session_state.submissions[response_index] = response
            st.session_state.score_message = (
                "Scores and feedback have been saved."
            )
            st.rerun()


# =======================================================
# Diagnostic profile
# =======================================================

elif page == "Diagnostic Profile":
    st.title("Diagnostic Profile")

    if not st.session_state.submissions:
        st.warning("No participant submissions are available.")

    else:
        participant_codes = sorted(
            {
                submission["student_id"]
                for submission in st.session_state.submissions
            }
        )

        selected_participant = st.selectbox(
            "Select Participant Code",
            participant_codes,
            key="diagnostic_participant_selector",
        )

        participant_submissions = [
            submission
            for submission in st.session_state.submissions
            if submission["student_id"] == selected_participant
        ]

        scored_submissions = [
            submission
            for submission in participant_submissions
            if submission.get("scores")
        ]

        first_submission = participant_submissions[0]

        st.markdown(
            f'### {first_submission["name"]} '
            f'({selected_participant})'
        )
        st.write(
            f'**Semester:** {first_submission["semester"]}'
        )

        metric_col1, metric_col2, metric_col3 = st.columns(3)
        metric_col1.metric(
            "Tasks Submitted",
            len(participant_submissions),
        )
        metric_col2.metric(
            "Tasks Scored",
            len(scored_submissions),
        )

        if scored_submissions:
            overall_percentage = (
                sum(
                    score_total(submission)
                    for submission in scored_submissions
                )
                / (len(scored_submissions) * RUBRIC_MAXIMUM)
            ) * 100

            metric_col3.metric(
                "Overall Percentage",
                f"{overall_percentage:.2f}%",
            )

            averages: dict[str, float] = {}

            for key in RUBRIC:
                averages[key] = sum(
                    int(submission["scores"][key])
                    for submission in scored_submissions
                ) / len(scored_submissions)

            strongest_key = max(averages, key=averages.get)
            weakest_key = min(averages, key=averages.get)

            st.markdown("## Diagnostic Summary")
            summary_col1, summary_col2 = st.columns(2)

            summary_col1.success(
                f"Strongest area: {RUBRIC[strongest_key]} "
                f"({averages[strongest_key]:.2f}/5)"
            )
            summary_col2.warning(
                f"Priority area: {RUBRIC[weakest_key]} "
                f"({averages[weakest_key]:.2f}/5)"
            )

            st.markdown("## Dimension-Wise Profile")

            for key, label in RUBRIC.items():
                average = averages[key]
                st.write(f"**{label}: {average:.2f}/5**")
                st.progress(average / 5)

            st.markdown("## Task-Wise Performance")

            task_rows = [
                {
                    "Task": submission["task_id"],
                    "Subject": submission["pedagogy_subject"],
                    "Total": score_total(submission),
                    "Maximum": RUBRIC_MAXIMUM,
                    "Percentage": round(
                        score_percentage(submission),
                        2,
                    ),
                    "Scored Time": submission.get("scored_time", ""),
                }
                for submission in scored_submissions
            ]

            st.dataframe(
                task_rows,
                use_container_width=True,
                hide_index=True,
            )

            st.markdown("## Teacher-Educator Feedback")

            for submission in scored_submissions:
                with st.expander(
                    f'{submission["task_id"]} â€” '
                    f'{submission["task_category"]}'
                ):
                    st.write(
                        submission.get(
                            "teacher_feedback",
                            "No written feedback.",
                        )
                    )

        else:
            metric_col3.metric("Overall Percentage", "Not available")
            st.info(
                "This participant's responses have not yet been scored."
            )


# =======================================================
# Task analytics
# =======================================================

elif page == "Task Analytics":
    st.title("Task Analytics")

    submissions = st.session_state.submissions
    scored_submissions = [
        submission
        for submission in submissions
        if submission.get("scores")
    ]

    participant_count = len(
        {
            submission["student_id"]
            for submission in submissions
        }
    )

    subject_count = len(
        {
            submission["pedagogy_subject"]
            for submission in submissions
        }
    )

    average_percentage = (
        sum(score_percentage(submission) for submission in scored_submissions)
        / len(scored_submissions)
        if scored_submissions
        else 0.0
    )

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

    metric_col1.metric("Submissions", len(submissions))
    metric_col2.metric("Participants", participant_count)
    metric_col3.metric("Scored Responses", len(scored_submissions))
    metric_col4.metric(
        "Mean Percentage",
        (
            f"{average_percentage:.2f}%"
            if scored_submissions
            else "Not available"
        ),
    )

    if not submissions:
        st.warning(
            "No submission data are available in the current session."
        )

    else:
        st.markdown("## Subject-Wise Summary")
        st.dataframe(
            aggregate_rows(submissions, "pedagogy_subject"),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("## Task-Wise Summary")
        st.dataframe(
            aggregate_rows(submissions, "task_id"),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("## Task-Category Summary")
        st.dataframe(
            aggregate_rows(submissions, "task_category"),
            use_container_width=True,
            hide_index=True,
        )

        if scored_submissions:
            st.markdown("## Overall Dimension Means")

            for key, label in RUBRIC.items():
                mean_score = sum(
                    int(submission["scores"][key])
                    for submission in scored_submissions
                ) / len(scored_submissions)

                st.write(f"**{label}: {mean_score:.2f}/5**")
                st.progress(mean_score / 5)

        st.markdown("## Participant Completion Status")

        participant_rows = []

        for participant in sorted(
            {
                submission["student_id"]
                for submission in submissions
            }
        ):
            participant_items = [
                submission
                for submission in submissions
                if submission["student_id"] == participant
            ]

            participant_rows.append(
                {
                    "Participant Code": participant,
                    "Name": participant_items[0]["name"],
                    "Submissions": len(participant_items),
                    "Scored": sum(
                        1
                        for submission in participant_items
                        if submission.get("scores")
                    ),
                }
            )

        st.dataframe(
            participant_rows,
            use_container_width=True,
            hide_index=True,
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
            "Download complete submission and scoring data as CSV",
            data=csv_data,
            file_name="VoiceBridge_PST_Submissions_and_Scores.csv",
            mime="text/csv",
        )

        st.caption(
            "The CSV contains participant details, task information, "
            "written responses, reflections, rubric scores, totals, "
            "percentages, feedback, and audio-file metadata."
        )

        st.markdown("## Data Preview")

        preview_rows = []

        for submission in st.session_state.submissions:
            preview_rows.append(
                {
                    "Participant": submission["student_id"],
                    "Name": submission["name"],
                    "Subject": submission["pedagogy_subject"],
                    "Task": submission["task_id"],
                    "Submitted": submission["submission_time"],
                    "Scored": "Yes" if submission.get("scores") else "No",
                    "Total": (
                        score_total(submission)
                        if submission.get("scores")
                        else ""
                    ),
                    "Percentage": (
                        round(score_percentage(submission), 2)
                        if submission.get("scores")
                        else ""
                    ),
                }
            )

        st.dataframe(
            preview_rows,
            use_container_width=True,
            hide_index=True,
        )

