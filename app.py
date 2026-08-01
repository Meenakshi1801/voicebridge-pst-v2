from __future__ import annotations

import csv
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st


# =======================================================
# PAGE CONFIGURATION
# =======================================================

# Unicode escape prevents the microphone icon from becoming corrupted.
MIC_ICON = "\U0001F399"

st.set_page_config(
    page_title="VoiceBridge-PST",
    page_icon=MIC_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

IST = ZoneInfo("Asia/Kolkata")

APP_DIR = Path(__file__).resolve().parent
PROFILE_IMAGE = APP_DIR / "MD_pic.png"


# =======================================================
# SUBJECT-WISE TASK BANK
# =======================================================

TASK_BANK: dict[str, list[tuple[str, str, str]]] = {
    "Pedagogy of Mathematics": [
        (
            "MATH-01",
            "Misconception Diagnosis",
            "A Class VI student says that a larger denominator means a larger "
            "fraction. How will you respond as a teacher?",
        ),
        (
            "MATH-02",
            "Error Analysis",
            "A student solves 3x + 5 = 20 as 3x = 25. How will you identify "
            "and address this error?",
        ),
        (
            "MATH-03",
            "Concept Explanation",
            "How would you explain the difference between area and perimeter "
            "to Class VII students?",
        ),
    ],

    "Pedagogy of Science": [
        (
            "SCI-01",
            "Misconception Diagnosis",
            "A Class VII student says that heat and temperature are the same. "
            "How will you respond as a teacher?",
        ),
        (
            "SCI-02",
            "Concept Explanation",
            "How would you introduce evaporation through a familiar daily-life "
            "situation?",
        ),
        (
            "SCI-03",
            "Short Activity Design",
            "Suggest a short classroom activity to demonstrate that air occupies "
            "space.",
        ),
    ],

    "Pedagogy of Social Science": [
        (
            "SOC-01",
            "Misconception Diagnosis",
            "A Class VIII student says that democracy only means voting. How will "
            "you respond as a teacher?",
        ),
        (
            "SOC-02",
            "Concept Explanation",
            "How would you explain equality and equity through a classroom or "
            "community example?",
        ),
        (
            "SOC-03",
            "Classroom Engagement",
            "Students find history dates boring and disconnected from life. What "
            "teaching strategy will you use?",
        ),
    ],

    "Pedagogy of English": [
        (
            "ENG-01",
            "Learner Support",
            "A student can read a passage aloud but cannot infer its meaning. How "
            "will you support the learner?",
        ),
        (
            "ENG-02",
            "Classroom Engagement",
            "Students hesitate to speak in English during class. What will you do?",
        ),
        (
            "ENG-03",
            "Assessment Decision",
            "After teaching a poem, how would you assess comprehension beyond "
            "memorisation?",
        ),
    ],

    "Pedagogy of Hindi": [
        (
            "HIN-01",
            "Misconception Diagnosis",
            "A student memorises a poem but cannot explain its meaning. How will "
            "you respond?",
        ),
        (
            "HIN-02",
            "Concept Explanation",
            "How would you introduce idioms through daily-life situations?",
        ),
        (
            "HIN-03",
            "Classroom Engagement",
            "Students are not interested in reading a Hindi passage aloud. What "
            "will you do?",
        ),
    ],

    "Pedagogy of Commerce": [
        (
            "COM-01",
            "Misconception Diagnosis",
            "A student says that sales and profit are the same. How will you respond?",
        ),
        (
            "COM-02",
            "Concept Explanation",
            "How would you explain assets and liabilities using examples from daily "
            "life?",
        ),
        (
            "COM-03",
            "Classroom Engagement",
            "Students find accounting rules mechanical and boring. What teaching "
            "strategy will you use?",
        ),
    ],

    "Pedagogy of Computer Science": [
        (
            "CS-01",
            "Misconception Diagnosis",
            "A student says that the internet and the web are the same. How will "
            "you respond?",
        ),
        (
            "CS-02",
            "Concept Explanation",
            "How would you explain an algorithm using a daily-life example?",
        ),
        (
            "CS-03",
            "Inclusive Adaptation",
            "How would you support a learner who has limited access to a computer "
            "outside the classroom?",
        ),
    ],
}


# =======================================================
# SCORING RUBRIC
# =======================================================

RUBRIC: list[tuple[str, str]] = [
    (
        "conceptual_clarity",
        "Conceptual Clarity",
    ),
    (
        "pedagogical_reasoning",
        "Pedagogical Reasoning",
    ),
    (
        "learner_centred_explanation",
        "Learner-Centred Explanation",
    ),
    (
        "misconception_diagnosis",
        "Misconception Diagnosis",
    ),
    (
        "use_of_example_strategy",
        "Use of Example / Teaching Strategy",
    ),
    (
        "reflective_thinking",
        "Reflective Thinking",
    ),
    (
        "voice_written_alignment",
        "Voice-Written Alignment",
    ),
]

RUBRIC_LABELS = dict(RUBRIC)

MAX_SCORE = len(RUBRIC) * 5


# =======================================================
# SESSION STORAGE
# =======================================================

if "submissions" not in st.session_state:
    st.session_state.submissions = []

if "activity_form_version" not in st.session_state:
    st.session_state.activity_form_version = 0

if "score_form_version" not in st.session_state:
    st.session_state.score_form_version = 0


# =======================================================
# HELPER FUNCTIONS
# =======================================================

def now_ist() -> datetime:
    """Return the current date and time in India."""

    return datetime.now(IST)


def make_reference(
    student_id: str,
    task_id: str,
) -> str:
    """Create a unique submission reference."""

    safe_student_id = "".join(
        character
        for character in student_id.upper()
        if character.isalnum()
    )

    timestamp = now_ist().strftime(
        "%Y%m%d%H%M%S%f"
    )

    return (
        f"{safe_student_id}-"
        f"{task_id}-"
        f"{timestamp}"
    )


def response_label(
    submission: dict[str, Any],
) -> str:
    """Create the label shown in response selectors."""

    return (
        f'{submission["student_id"]} | '
        f'{submission["task_id"]} | '
        f'{submission["name"]} | '
        f'{submission["submission_time"]}'
    )


def response_selector(
    label: str,
    key: str,
    submissions: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """Display a selector and return the selected response."""

    available_submissions = (
        submissions
        if submissions is not None
        else st.session_state.submissions
    )

    if not available_submissions:
        return None

    references = [
        submission["submission_reference"]
        for submission in available_submissions
    ]

    labels = {
        submission["submission_reference"]:
        response_label(submission)
        for submission in available_submissions
    }

    selected_reference = st.selectbox(
        label,
        references,
        format_func=lambda reference: labels[reference],
        key=key,
    )

    return next(
        (
            submission
            for submission in available_submissions
            if submission["submission_reference"]
            == selected_reference
        ),
        None,
    )


def generate_feedback(
    scores: dict[str, int],
) -> str:
    """Generate basic diagnostic feedback."""

    strongest_dimension = max(
        scores,
        key=scores.get,
    )

    weakest_dimension = min(
        scores,
        key=scores.get,
    )

    guidance = {
        "conceptual_clarity": (
            "Clarify the central concept and use precise "
            "subject terminology."
        ),

        "pedagogical_reasoning": (
            "Explain why the proposed teaching response "
            "is appropriate for the learner."
        ),

        "learner_centred_explanation": (
            "Connect the explanation more directly with "
            "learners' prior knowledge and needs."
        ),

        "misconception_diagnosis": (
            "Identify the exact misconception or source "
            "of error more precisely."
        ),

        "use_of_example_strategy": (
            "Use a clearer example, activity, analogy, "
            "or assessment strategy."
        ),

        "reflective_thinking": (
            "Add deeper reflection on limitations, "
            "alternatives, and possible improvement."
        ),

        "voice_written_alignment": (
            "Improve consistency between the oral "
            "reasoning and written response."
        ),
    }

    return (
        f"Strongest area: "
        f"{RUBRIC_LABELS[strongest_dimension]}. "
        f"Priority for improvement: "
        f"{RUBRIC_LABELS[weakest_dimension]}. "
        f"Suggested action: "
        f"{guidance[weakest_dimension]}"
    )


def submissions_to_csv(
    submissions: list[dict[str, Any]],
) -> bytes:
    """Convert submission data into a CSV file."""

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
        *[
            rubric_key
            for rubric_key, _ in RUBRIC
        ],
        "total_score",
        "percentage",
        "teacher_feedback",
        "scored_time",
    ]

    writer = csv.DictWriter(
        output,
        fieldnames=fields,
    )

    writer.writeheader()

    for submission in submissions:

        row = {
            field: submission.get(
                field,
                "",
            )
            for field in fields
        }

        for rubric_key, _ in RUBRIC:

            row[rubric_key] = submission.get(
                "scores",
                {},
            ).get(
                rubric_key,
                "",
            )

        percentage = row.get(
            "percentage"
        )

        if isinstance(
            percentage,
            (int, float),
        ):

            row["percentage"] = round(
                float(percentage),
                2,
            )

        writer.writerow(
            row
        )

    return output.getvalue().encode(
        "utf-8-sig"
    )


def show_response_content(
    submission: dict[str, Any],
) -> None:
    """Display the complete participant response."""

    st.markdown(
        "### Pedagogical Prompt"
    )

    st.info(
        submission["prompt"]
    )

    st.markdown(
        "### Voice Reasoning"
    )

    st.audio(
        submission["audio_bytes"],
        format=submission.get(
            "audio_mime_type",
            "audio/wav",
        ),
    )

    st.markdown(
        "### Written Pedagogical Response"
    )

    st.write(
        submission["written_response"]
    )

    st.markdown(
        "### Reflection: Identified Issue"
    )

    st.write(
        submission["reflection_issue"]
    )

    st.markdown(
        "### Reflection: Proposed Strategy"
    )

    st.write(
        submission["reflection_strategy"]
    )


# =======================================================
# HOME PAGE
# =======================================================

def render_home() -> None:

    st.markdown(
        f"# {MIC_ICON} VoiceBridge-PST Dashboard"
    )

    st.subheader(
        "Voice-First Micro-Pedagogical Reasoning "
        "Activity and Analytics Platform"
    )

    st.write("")

    photograph_column, information_column = st.columns(
        [1, 2.6],
        gap="large",
    )

    with photograph_column:

        if PROFILE_IMAGE.exists():

            st.image(
                str(PROFILE_IMAGE),
                width=240,
            )

        else:

            st.warning(
                "Profile photograph not found. "
                "Upload MD_pic.png in the same "
                "folder as app.py."
            )

    with information_column:

        st.caption(
            "Conceptualized and Developed by"
        )

        st.markdown(
            "### Dr. Meenakshi Dwivedi"
        )

        st.markdown(
            "Assistant Professor  \n"
            "Department of Education / School of Education  \n"
            "Mahatma Jyotiba Phule Rohilkhand University  \n"
            "Bareilly, Uttar Pradesh, India"
        )

    st.divider()

    st.header(
        "Purpose"
    )

    st.write(
        "VoiceBridge-PST is a voice-first activity and "
        "analytics platform designed to support the "
        "assessment and development of micro-pedagogical "
        "reasoning among pre-service teachers."
    )

    st.header(
        "Activity Flow"
    )

    st.write(
        "Pedagogical Prompt → Voice Reasoning → "
        "Written Pedagogical Response → Reflective Response → "
        "Teacher-Educator Review → Rubric Scoring → "
        "Diagnostic Feedback"
    )

    st.header(
        "Assessment Dimensions"
    )

    for number, (_, label) in enumerate(
        RUBRIC,
        start=1,
    ):

        st.write(
            f"{number}. {label}"
        )


# =======================================================
# ACTIVITY SUBMISSION PAGE
# =======================================================

def render_activity_submission() -> None:

    st.title(
        "Activity Submission"
    )

    if "activity_flash" in st.session_state:

        flash = st.session_state.pop(
            "activity_flash"
        )

        st.success(
            flash["message"]
        )

        st.info(
            f'Submission reference: '
            f'{flash["reference"]}'
        )

    st.write(
        "Select your pedagogy subject and task. "
        "Then record your voice reasoning and "
        "complete the written and reflective responses."
    )

    selected_subject = st.selectbox(
        "Pedagogy Subject",
        list(TASK_BANK),
        key="selected_subject",
    )

    tasks = TASK_BANK[
        selected_subject
    ]

    task_labels = [
        f"{task_id} - {category}"
        for task_id, category, _ in tasks
    ]

    selected_task_label = st.selectbox(
        "Task",
        task_labels,
        key=f"selected_task_{selected_subject}",
    )

    selected_task_index = task_labels.index(
        selected_task_label
    )

    task_id, task_category, prompt = tasks[
        selected_task_index
    ]

    st.markdown(
        "### Pedagogical Prompt"
    )

    st.info(
        prompt
    )

    task_column_1, task_column_2 = st.columns(
        2
    )

    task_column_1.text_input(
        "Task ID",
        value=task_id,
        disabled=True,
    )

    task_column_2.text_input(
        "Task Category",
        value=task_category,
        disabled=True,
    )

    st.divider()

    st.markdown(
        "## Stage 1: Voice Reasoning"
    )

    st.write(
        "Think aloud and explain how you understand "
        "the pedagogical situation and how you would "
        "respond as a teacher."
    )

    st.caption(
        "Suggested duration: 2-3 minutes. "
        "Allow microphone access when requested."
    )

    form_version = (
        st.session_state.activity_form_version
    )

    audio_response = st.audio_input(
        "Record your voice response",
        key=(
            f"audio_{task_id}_"
            f"{form_version}"
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

    with st.form(
        f"activity_form_{form_version}"
    ):

        st.markdown(
            "## Participant Details"
        )

        participant_column_1, participant_column_2 = (
            st.columns(2)
        )

        with participant_column_1:

            student_id = st.text_input(
                "Student ID / Participant Code",
                placeholder="Example: PST001",
            )

            participant_name = st.text_input(
                "Name",
                placeholder="Enter your name",
            )

        with participant_column_2:

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

        st.markdown(
            "## Stage 2: Written Pedagogical Response"
        )

        written_response = st.text_area(
            "Explain how you would respond to the "
            "pedagogical situation.",
            placeholder=(
                "Describe what you would say or do as "
                "a teacher and explain the reasoning "
                "behind your response."
            ),
            height=180,
        )

        st.caption(
            "Suggested length: approximately "
            "150-200 words."
        )

        st.markdown(
            "## Stage 3: Reflective Response"
        )

        reflection_issue = st.text_area(
            "What learner difficulty, misconception, "
            "error, or pedagogical issue did you identify?",
            height=120,
        )

        reflection_strategy = st.text_area(
            "What example, activity, explanation, "
            "assessment method, or teaching strategy "
            "would you use?",
            height=120,
        )

        declaration = st.checkbox(
            "I confirm that the voice and written "
            "responses are my own work."
        )

        submit_response = st.form_submit_button(
            "Submit Activity",
            type="primary",
        )

    if not submit_response:
        return

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
            "Please complete the following "
            "before submitting:"
        )

        for error in errors:

            st.write(
                f"- {error}"
            )

        return

    submission_reference = make_reference(
        student_id.strip(),
        task_id,
    )

    submission: dict[str, Any] = {
        "submission_reference":
        submission_reference,

        "student_id":
        student_id.strip(),

        "name":
        participant_name.strip(),

        "semester":
        semester,

        "pedagogy_subject":
        selected_subject,

        "task_id":
        task_id,

        "task_category":
        task_category,

        "prompt":
        prompt,

        "audio_bytes":
        audio_response.getvalue(),

        "audio_file_name":
        getattr(
            audio_response,
            "name",
            f"{submission_reference}.wav",
        ),

        "audio_mime_type":
        getattr(
            audio_response,
            "type",
            "audio/wav",
        ),

        "written_response":
        written_response.strip(),

        "reflection_issue":
        reflection_issue.strip(),

        "reflection_strategy":
        reflection_strategy.strip(),

        "submission_time":
        now_ist().strftime(
            "%d-%m-%Y %I:%M %p"
        ),

        "scores":
        {},

        "total_score":
        None,

        "percentage":
        None,

        "teacher_feedback":
        "",

        "scored_time":
        "",
    }

    st.session_state.submissions.append(
        submission
    )

    st.session_state.activity_flash = {
        "message":
        "Your activity has been submitted successfully.",

        "reference":
        submission_reference,
    }

    st.session_state.activity_form_version += 1

    st.rerun()


# =======================================================
# REVIEW RESPONSES PAGE
# =======================================================

def render_review_responses() -> None:

    st.title(
        "Review Responses"
    )

    if not st.session_state.submissions:

        st.warning(
            "No responses have been submitted "
            "in the current session."
        )

        return

    selected_submission = response_selector(
        "Select a response",
        "review_reference",
    )

    if selected_submission is None:
        return

    st.divider()

    detail_column_1, detail_column_2, detail_column_3 = (
        st.columns(3)
    )

    detail_column_1.metric(
        "Participant Code",
        selected_submission["student_id"],
    )

    detail_column_2.metric(
        "Task",
        selected_submission["task_id"],
    )

    detail_column_3.metric(
        "Semester",
        selected_submission["semester"],
    )

    st.markdown(
        "### Participant Information"
    )

    st.write(
        f'**Name:** '
        f'{selected_submission["name"]}'
    )

    st.write(
        f'**Pedagogy Subject:** '
        f'{selected_submission["pedagogy_subject"]}'
    )

    st.write(
        f'**Task Category:** '
        f'{selected_submission["task_category"]}'
    )

    st.write(
        f'**Submission Time:** '
        f'{selected_submission["submission_time"]}'
    )

    st.write(
        f'**Reference:** '
        f'{selected_submission["submission_reference"]}'
    )

    show_response_content(
        selected_submission
    )

    st.download_button(
        "Download this audio recording",
        data=selected_submission["audio_bytes"],
        file_name=selected_submission.get(
            "audio_file_name",
            "voice_response.wav",
        ),
        mime=selected_submission.get(
            "audio_mime_type",
            "audio/wav",
        ),
    )

    if not selected_submission.get(
        "scores"
    ):
        return

    st.markdown(
        "### Saved Rubric Scores"
    )

    score_dataframe = pd.DataFrame(
        {
            "Dimension": [
                label
                for _, label in RUBRIC
            ],

            "Score": [
                selected_submission[
                    "scores"
                ].get(
                    rubric_key,
                    "",
                )
                for rubric_key, _ in RUBRIC
            ],
        }
    )

    st.dataframe(
        score_dataframe,
        hide_index=True,
        use_container_width=True,
    )

    score_column_1, score_column_2 = st.columns(
        2
    )

    score_column_1.metric(
        "Total Score",
        (
            f'{selected_submission["total_score"]}'
            f'/{MAX_SCORE}'
        ),
    )

    percentage_value = float(
        selected_submission.get(
            "percentage"
        )
        or 0.0
    )

    score_column_2.metric(
        "Percentage",
        f"{percentage_value:.2f}%",
    )

    st.markdown(
        "### Teacher-Educator Feedback"
    )

    st.info(
        selected_submission.get(
            "teacher_feedback",
            "",
        )
    )


# =======================================================
# SCORE RESPONSES PAGE
# =======================================================

def render_score_responses() -> None:

    st.title(
        "Score Responses"
    )

    if "score_flash" in st.session_state:

        st.success(
            st.session_state.pop(
                "score_flash"
            )
        )

    if not st.session_state.submissions:

        st.warning(
            "No responses are available for scoring "
            "in the current session."
        )

        return

    selected_submission = response_selector(
        "Select a response to score",
        "score_reference",
    )

    if selected_submission is None:
        return

    with st.expander(
        "Review participant response before scoring",
        expanded=True,
    ):

        show_response_content(
            selected_submission
        )

    st.markdown(
        "### Rubric Scoring"
    )

    st.caption(
        "1 = Very weak, 2 = Weak, "
        "3 = Satisfactory, 4 = Good, "
        "5 = Excellent."
    )

    existing_scores = selected_submission.get(
        "scores",
        {},
    )

    score_version = (
        st.session_state.score_form_version
    )

    reference = selected_submission[
        "submission_reference"
    ]

    with st.form(
        f"score_form_{reference}_{score_version}"
    ):

        entered_scores: dict[str, int] = {}

        left_column, right_column = (
            st.columns(2)
        )

        for index, (
            rubric_key,
            rubric_label,
        ) in enumerate(RUBRIC):

            target_column = (
                left_column
                if index % 2 == 0
                else right_column
            )

            with target_column:

                entered_scores[
                    rubric_key
                ] = st.slider(
                    rubric_label,
                    min_value=1,
                    max_value=5,
                    value=int(
                        existing_scores.get(
                            rubric_key,
                            3,
                        )
                    ),
                    step=1,
                    key=(
                        f"score_{reference}_"
                        f"{rubric_key}_"
                        f"{score_version}"
                    ),
                )

        calculated_total = sum(
            entered_scores.values()
        )

        calculated_percentage = (
            calculated_total
            / MAX_SCORE
            * 100
        )

        metric_column_1, metric_column_2 = (
            st.columns(2)
        )

        metric_column_1.metric(
            "Calculated Total",
            (
                f"{calculated_total}"
                f"/{MAX_SCORE}"
            ),
        )

        metric_column_2.metric(
            "Calculated Percentage",
            f"{calculated_percentage:.2f}%",
        )

        teacher_feedback = st.text_area(
            "Teacher-Educator Feedback",
            value=selected_submission.get(
                "teacher_feedback",
                "",
            ),
            height=140,
            placeholder=(
                "Leave blank to use automatically "
                "generated diagnostic feedback."
            ),
            key=(
                f"feedback_{reference}_"
                f"{score_version}"
            ),
        )

        save_scores = st.form_submit_button(
            "Save Scores and Feedback",
            type="primary",
        )

    if not save_scores:
        return

    selected_submission[
        "scores"
    ] = entered_scores

    selected_submission[
        "total_score"
    ] = calculated_total

    selected_submission[
        "percentage"
    ] = calculated_percentage

    selected_submission[
        "teacher_feedback"
    ] = (
        teacher_feedback.strip()
        or generate_feedback(
            entered_scores
        )
    )

    selected_submission[
        "scored_time"
    ] = now_ist().strftime(
        "%d-%m-%Y %I:%M %p"
    )

    st.session_state.score_flash = (
        f'Scores saved for '
        f'{selected_submission["student_id"]} - '
        f'{selected_submission["task_id"]}.'
    )

    st.session_state.score_form_version += 1

    st.rerun()


# =======================================================
# DIAGNOSTIC PROFILE PAGE
# =======================================================

def render_diagnostic_profile() -> None:

    st.title(
        "Diagnostic Profile"
    )

    scored_submissions = [
        submission
        for submission in st.session_state.submissions
        if submission.get(
            "scores"
        )
    ]

    if not scored_submissions:

        st.warning(
            "No scored responses are available "
            "in the current session."
        )

        return

    participant_ids = sorted(
        {
            submission["student_id"]
            for submission in scored_submissions
        }
    )

    selected_student_id = st.selectbox(
        "Select Participant Code",
        participant_ids,
    )

    participant_submissions = [
        submission
        for submission in scored_submissions
        if submission["student_id"]
        == selected_student_id
    ]

    st.subheader(
        f"Diagnostic Profile: "
        f"{selected_student_id}"
    )

    profile_column_1, profile_column_2, profile_column_3 = (
        st.columns(3)
    )

    profile_column_1.metric(
        "Name",
        participant_submissions[0]["name"],
    )

    profile_column_2.metric(
        "Semester",
        participant_submissions[0]["semester"],
    )

    profile_column_3.metric(
        "Scored Tasks",
        len(
            participant_submissions
        ),
    )

    dimension_means = {
        rubric_key: (
            sum(
                submission["scores"][
                    rubric_key
                ]
                for submission
                in participant_submissions
            )
            / len(
                participant_submissions
            )
        )
        for rubric_key, _ in RUBRIC
    }

    average_percentage = (
        sum(
            float(
                submission["percentage"]
            )
            for submission
            in participant_submissions
        )
        / len(
            participant_submissions
        )
    )

    strongest_dimension = max(
        dimension_means,
        key=dimension_means.get,
    )

    weakest_dimension = min(
        dimension_means,
        key=dimension_means.get,
    )

    summary_column_1, summary_column_2, summary_column_3 = (
        st.columns(
            [1, 1.4, 1.4]
        )
    )

    with summary_column_1:

        st.metric(
            "Average Percentage",
            f"{average_percentage:.2f}%",
        )

    with summary_column_2:

        st.caption(
            "Strongest Area"
        )

        st.success(
            RUBRIC_LABELS[
                strongest_dimension
            ]
        )

    with summary_column_3:

        st.caption(
            "Priority Area"
        )

        st.warning(
            RUBRIC_LABELS[
                weakest_dimension
            ]
        )

    st.markdown(
        "### Dimension-Wise Profile"
    )

    profile_dataframe = pd.DataFrame(
        {
            "Dimension": [
                label
                for _, label in RUBRIC
            ],

            "Average Score": [
                round(
                    dimension_means[
                        rubric_key
                    ],
                    2,
                )
                for rubric_key, _ in RUBRIC
            ],
        }
    )

    st.bar_chart(
        profile_dataframe,
        x="Average Score",
        y="Dimension",
        horizontal=True,
        height=380,
    )

    st.markdown(
        "### Task-Wise Performance"
    )

    task_dataframe = pd.DataFrame(
        [
            {
                "Task":
                submission["task_id"],

                "Subject":
                submission[
                    "pedagogy_subject"
                ],

                "Total Score":
                submission[
                    "total_score"
                ],

                "Percentage":
                round(
                    float(
                        submission[
                            "percentage"
                        ]
                    ),
                    2,
                ),

                "Scored Time":
                submission[
                    "scored_time"
                ],
            }

            for submission
            in participant_submissions
        ]
    )

    st.dataframe(
        task_dataframe,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Subject":
            st.column_config.TextColumn(
                "Pedagogy Subject",
                width="large",
            ),

            "Percentage":
            st.column_config.NumberColumn(
                "Percentage (%)",
                format="%.2f",
            ),
        },
    )

    st.markdown(
        "### Latest Diagnostic Feedback"
    )

    st.info(
        participant_submissions[-1].get(
            "teacher_feedback",
            "",
        )
    )


# =======================================================
# TASK ANALYTICS PAGE
# =======================================================

def render_task_analytics() -> None:

    st.title(
        "Task Analytics"
    )

    scored_submissions = [
        submission
        for submission in st.session_state.submissions
        if submission.get(
            "scores"
        )
    ]

    (
        analytics_column_1,
        analytics_column_2,
        analytics_column_3,
        analytics_column_4,
    ) = st.columns(4)

    analytics_column_1.metric(
        "Participants",
        len(
            {
                submission["student_id"]
                for submission
                in st.session_state.submissions
            }
        ),
    )

    analytics_column_2.metric(
        "Submissions",
        len(
            st.session_state.submissions
        ),
    )

    analytics_column_3.metric(
        "Scored Responses",
        len(
            scored_submissions
        ),
    )

    mean_percentage = (
        sum(
            float(
                submission["percentage"]
            )
            for submission
            in scored_submissions
        )
        / len(
            scored_submissions
        )
        if scored_submissions
        else 0.0
    )

    analytics_column_4.metric(
        "Mean Percentage",
        f"{mean_percentage:.2f}%",
    )

    if not scored_submissions:

        st.warning(
            "No scored data are available "
            "for analytics."
        )

        return

    analytics_dataframe = pd.DataFrame(
        [
            {
                "Participant":
                submission["student_id"],

                "Subject":
                submission[
                    "pedagogy_subject"
                ],

                "Task":
                submission[
                    "task_id"
                ],

                "Category":
                submission[
                    "task_category"
                ],

                "Total Score":
                submission[
                    "total_score"
                ],

                "Percentage":
                round(
                    float(
                        submission[
                            "percentage"
                        ]
                    ),
                    2,
                ),

                **{
                    rubric_label:
                    submission["scores"][
                        rubric_key
                    ]

                    for rubric_key, rubric_label
                    in RUBRIC
                },
            }

            for submission
            in scored_submissions
        ]
    )

    st.markdown(
        "### Subject-Wise Mean Percentage"
    )

    subject_summary = (
        analytics_dataframe
        .groupby(
            "Subject",
            as_index=False,
        )["Percentage"]
        .mean()
        .sort_values(
            "Percentage",
            ascending=False,
        )
    )

    subject_summary["Percentage"] = (
        subject_summary[
            "Percentage"
        ].round(2)
    )

    if len(
        subject_summary
    ) == 1:

        st.metric(
            subject_summary.iloc[0][
                "Subject"
            ],
            f'{subject_summary.iloc[0]["Percentage"]:.2f}%',
        )

    else:

        st.bar_chart(
            subject_summary,
            x="Percentage",
            y="Subject",
            horizontal=True,
            height=300,
        )

    st.dataframe(
        subject_summary,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Subject":
            st.column_config.TextColumn(
                "Pedagogy Subject",
                width="large",
            ),

            "Percentage":
            st.column_config.NumberColumn(
                "Mean Percentage (%)",
                format="%.2f",
            ),
        },
    )

    st.markdown(
        "### Task-Wise Mean Percentage"
    )

    task_summary = (
        analytics_dataframe
        .groupby(
            "Task",
            as_index=False,
        )["Percentage"]
        .mean()
        .sort_values(
            "Task"
        )
    )

    task_summary["Percentage"] = (
        task_summary[
            "Percentage"
        ].round(2)
    )

    st.bar_chart(
        task_summary,
        x="Task",
        y="Percentage",
        height=300,
    )

    st.dataframe(
        task_summary,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Percentage":
            st.column_config.NumberColumn(
                "Mean Percentage (%)",
                format="%.2f",
            ),
        },
    )

    st.markdown(
        "### Category-Wise Mean Percentage"
    )

    category_summary = (
        analytics_dataframe
        .groupby(
            "Category",
            as_index=False,
        )["Percentage"]
        .mean()
        .sort_values(
            "Percentage",
            ascending=False,
        )
    )

    category_summary["Percentage"] = (
        category_summary[
            "Percentage"
        ].round(2)
    )

    st.dataframe(
        category_summary,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Category":
            st.column_config.TextColumn(
                "Task Category",
                width="large",
            ),

            "Percentage":
            st.column_config.NumberColumn(
                "Mean Percentage (%)",
                format="%.2f",
            ),
        },
    )

    st.markdown(
        "### Dimension-Wise Mean Scores"
    )

    dimension_summary = pd.DataFrame(
        {
            "Dimension": [
                rubric_label
                for _, rubric_label in RUBRIC
            ],

            "Mean Score": [
                round(
                    float(
                        analytics_dataframe[
                            rubric_label
                        ].mean()
                    ),
                    2,
                )

                for _, rubric_label in RUBRIC
            ],
        }
    )

    st.bar_chart(
        dimension_summary,
        x="Mean Score",
        y="Dimension",
        horizontal=True,
        height=380,
    )

    st.markdown(
        "### Scored Dataset Summary"
    )

    summary_columns = [
        "Participant",
        "Subject",
        "Task",
        "Category",
        "Total Score",
        "Percentage",
    ]

    st.dataframe(
        analytics_dataframe[
            summary_columns
        ],
        hide_index=True,
        use_container_width=True,
        column_config={
            "Participant":
            st.column_config.TextColumn(
                "Participant Code"
            ),

            "Subject":
            st.column_config.TextColumn(
                "Pedagogy Subject",
                width="large",
            ),

            "Category":
            st.column_config.TextColumn(
                "Task Category",
                width="large",
            ),

            "Total Score":
            st.column_config.NumberColumn(
                "Total Score",
                format="%d",
            ),

            "Percentage":
            st.column_config.NumberColumn(
                "Percentage (%)",
                format="%.2f",
            ),
        },
    )

    with st.expander(
        "View Complete Dimension-Wise Dataset"
    ):

        st.dataframe(
            analytics_dataframe,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Percentage":
                st.column_config.NumberColumn(
                    "Percentage (%)",
                    format="%.2f",
                ),
            },
        )


# =======================================================
# DOWNLOAD DATA PAGE
# =======================================================

def render_download_data() -> None:

    st.title(
        "Download Data"
    )

    if not st.session_state.submissions:

        st.warning(
            "No responses are available for download "
            "in the current session."
        )

        return

    st.download_button(
        "Download Complete Submission Data as CSV",
        data=submissions_to_csv(
            st.session_state.submissions
        ),
        file_name=(
            "VoiceBridge_PST_"
            "Submissions_and_Scores.csv"
        ),
        mime="text/csv",
        type="primary",
    )

    st.caption(
        "The CSV includes participant details, task "
        "information, written responses, reflections, "
        "rubric scores, total score, percentage, teacher "
        "feedback, and audio-file metadata. Audio "
        "recordings can be downloaded individually from "
        "Review Responses."
    )

    preview_dataframe = pd.DataFrame(
        [
            {
                "Reference":
                submission[
                    "submission_reference"
                ],

                "Participant":
                submission[
                    "student_id"
                ],

                "Name":
                submission[
                    "name"
                ],

                "Subject":
                submission[
                    "pedagogy_subject"
                ],

                "Task":
                submission[
                    "task_id"
                ],

                "Scored":
                (
                    "Yes"
                    if submission.get(
                        "scores"
                    )
                    else "No"
                ),

                "Total Score":
                submission.get(
                    "total_score",
                    "",
                ),

                "Percentage":
                submission.get(
                    "percentage",
                    "",
                ),
            }

            for submission
            in st.session_state.submissions
        ]
    )

    preview_dataframe["Percentage"] = pd.to_numeric(
        preview_dataframe[
            "Percentage"
        ],
        errors="coerce",
    ).round(2)

    st.markdown(
        "### Data Preview"
    )

    st.dataframe(
        preview_dataframe,
        hide_index=True,
        use_container_width=True,
        column_order=[
            "Participant",
            "Name",
            "Subject",
            "Task",
            "Scored",
            "Total Score",
            "Percentage",
            "Reference",
        ],
        column_config={
            "Reference":
            st.column_config.TextColumn(
                "Submission Reference",
                width="large",
            ),

            "Subject":
            st.column_config.TextColumn(
                "Pedagogy Subject",
                width="large",
            ),

            "Percentage":
            st.column_config.NumberColumn(
                "Percentage (%)",
                format="%.2f",
            ),
        },
    )


# =======================================================
# SIDEBAR
# =======================================================

st.sidebar.markdown(
    f"## {MIC_ICON} VoiceBridge-PST"
)

st.sidebar.caption(
    "Activity and Analytics Platform"
)

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
    len(
        st.session_state.submissions
    ),
)

st.sidebar.metric(
    "Scored responses",
    sum(
        1
        for submission
        in st.session_state.submissions
        if submission.get(
            "scores"
        )
    ),
)


# =======================================================
# PAGE ROUTING
# =======================================================

PAGES = {
    "Home":
    render_home,

    "Activity Submission":
    render_activity_submission,

    "Review Responses":
    render_review_responses,

    "Score Responses":
    render_score_responses,

    "Diagnostic Profile":
    render_diagnostic_profile,

    "Task Analytics":
    render_task_analytics,

    "Download Data":
    render_download_data,
}

PAGES[page]()