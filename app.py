from __future__ import annotations

import csv
from datetime import datetime
from io import StringIO
from typing import Any

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="VoiceBridge-PST",
    page_icon=":microphone:",
    layout="wide",
)


# =======================================================
# Subject-wise task bank
# =======================================================

TASK_BANK = {
    "Pedagogy of Mathematics": [
        (
            "MATH-01",
            "Misconception Diagnosis",
            "A Class VI student says that a larger denominator means a "
            "larger fraction. How will you respond as a teacher?",
        ),
        (
            "MATH-02",
            "Error Analysis",
            "A student solves 3x + 5 = 20 as 3x = 25. How will you "
            "identify and address this error?",
        ),
        (
            "MATH-03",
            "Concept Explanation",
            "How would you explain the difference between area and "
            "perimeter to Class VII students?",
        ),
    ],

    "Pedagogy of Science": [
        (
            "SCI-01",
            "Misconception Diagnosis",
            "A Class VII student says that heat and temperature are the "
            "same. How will you respond as a teacher?",
        ),
        (
            "SCI-02",
            "Concept Explanation",
            "How would you introduce evaporation through a familiar "
            "daily-life situation?",
        ),
        (
            "SCI-03",
            "Short Activity Design",
            "Suggest a short classroom activity to demonstrate that air "
            "occupies space.",
        ),
    ],

    "Pedagogy of Social Science": [
        (
            "SOC-01",
            "Misconception Diagnosis",
            "A Class VIII student says that democracy only means voting. "
            "How will you respond as a teacher?",
        ),
        (
            "SOC-02",
            "Concept Explanation",
            "How would you explain equality and equity through a "
            "classroom or community example?",
        ),
        (
            "SOC-03",
            "Classroom Engagement",
            "Students find history dates boring and disconnected from "
            "life. What teaching strategy will you use?",
        ),
    ],

    "Pedagogy of English": [
        (
            "ENG-01",
            "Learner Support",
            "A student can read a passage aloud but cannot infer its "
            "meaning. How will you support the learner?",
        ),
        (
            "ENG-02",
            "Classroom Engagement",
            "Students hesitate to speak in English during class. "
            "What will you do?",
        ),
        (
            "ENG-03",
            "Assessment Decision",
            "After teaching a poem, how would you assess comprehension "
            "beyond memorisation?",
        ),
    ],

    "Pedagogy of Hindi": [
        (
            "HIN-01",
            "Misconception Diagnosis",
            "A student memorises a poem but cannot explain its meaning. "
            "How will you respond?",
        ),
        (
            "HIN-02",
            "Concept Explanation",
            "How would you introduce idioms through daily-life situations?",
        ),
        (
            "HIN-03",
            "Classroom Engagement",
            "Students are not interested in reading a Hindi passage aloud. "
            "What will you do?",
        ),
    ],

    "Pedagogy of Commerce": [
        (
            "COM-01",
            "Misconception Diagnosis",
            "A student says that sales and profit are the same. "
            "How will you respond?",
        ),
        (
            "COM-02",
            "Concept Explanation",
            "How would you explain assets and liabilities using examples "
            "from daily life?",
        ),
        (
            "COM-03",
            "Classroom Engagement",
            "Students find accounting rules mechanical and boring. "
            "What teaching strategy will you use?",
        ),
    ],

    "Pedagogy of Computer Science": [
        (
            "CS-01",
            "Misconception Diagnosis",
            "A student says that the internet and the web are the same. "
            "How will you respond?",
        ),
        (
            "CS-02",
            "Concept Explanation",
            "How would you explain an algorithm using a daily-life example?",
        ),
        (
            "CS-03",
            "Inclusive Adaptation",
            "How would you support a learner who has limited access to "
            "a computer outside the classroom?",
        ),
    ],
}


# =======================================================
# Scoring rubric
# =======================================================

RUBRIC = [
    ("conceptual_clarity", "Conceptual Clarity"),
    ("pedagogical_reasoning", "Pedagogical Reasoning"),
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
# Session storage
# =======================================================

for key, default_value in {
    "submissions": [],
    "activity_form_version": 0,
    "score_form_version": 0,
}.items():

    if key not in st.session_state:
        st.session_state[key] = default_value


# =======================================================
# Helper functions
# =======================================================

def make_reference(
    student_id: str,
    task_id: str,
) -> str:

    safe_id = "".join(
        character
        for character in student_id.upper()
        if character.isalnum()
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d%H%M%S"
    )

    return f"{safe_id}-{task_id}-{timestamp}"


def response_label(
    submission: dict[str, Any],
) -> str:

    return (
        f'{submission["student_id"]} | '
        f'{submission["task_id"]} | '
        f'{submission["name"]} | '
        f'{submission["submission_time"]}'
    )


def get_submission(
    reference: str,
) -> dict[str, Any] | None:

    return next(
        (
            submission
            for submission in st.session_state.submissions
            if submission["submission_reference"] == reference
        ),
        None,
    )


def generate_feedback(
    scores: dict[str, int],
) -> str:

    strongest = max(
        scores,
        key=scores.get,
    )

    weakest = min(
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
        f"{RUBRIC_LABELS[strongest]}. "
        f"Priority for improvement: "
        f"{RUBRIC_LABELS[weakest]}. "
        f"Suggested action: "
        f"{guidance[weakest]}"
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

        writer.writerow(row)

    return output.getvalue().encode(
        "utf-8-sig"
    )


def response_selector(
    label: str,
    key: str,
) -> dict[str, Any] | None:

    references = [
        submission["submission_reference"]
        for submission in st.session_state.submissions
    ]

    labels = {
        submission["submission_reference"]:
        response_label(submission)
        for submission in st.session_state.submissions
    }

    selected_reference = st.selectbox(
        label,
        references,
        format_func=lambda reference: labels[
            reference
        ],
        key=key,
    )

    return get_submission(
        selected_reference
    )


# =======================================================
# Sidebar navigation
# =======================================================

st.sidebar.title(
    "VoiceBridge-PST"
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
    len(st.session_state.submissions),
)

st.sidebar.metric(
    "Scored responses",
    sum(
        1
        for submission
        in st.session_state.submissions
        if submission.get("scores")
    ),
)


# =======================================================
# Home
# =======================================================

if page == "Home":

    st.title(
        "VoiceBridge-PST Dashboard"
    )

    st.subheader(
        "Voice-First Micro-Pedagogical Reasoning "
        "Activity and Analytics Platform"
    )

    st.caption(
        "Conceptualized and Developed by"
    )

    st.markdown(
        "**Dr. Meenakshi Dwivedi**  \n"
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
        "VoiceBridge-PST is a voice-first activity "
        "and analytics platform for assessing "
        "micro-pedagogical reasoning among "
        "pre-service teachers."
    )

    st.header(
        "Activity Flow"
    )

    st.write(
        "Pedagogical prompt -> Voice reasoning -> "
        "Written pedagogical response -> Reflective "
        "response -> Teacher-educator review -> "
        "Rubric scoring -> Diagnostic feedback"
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
# Activity submission
# =======================================================

elif page == "Activity Submission":

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
        key="selected_task",
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

    task_col1, task_col2 = st.columns(
        2
    )

    task_col1.text_input(
        "Task ID",
        value=task_id,
        disabled=True,
    )

    task_col2.text_input(
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
        "Suggested duration: 2-3 minutes. Allow "
        "microphone access when requested."
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

        participant_col1, participant_col2 = (
            st.columns(2)
        )

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

        submit_response = (
            st.form_submit_button(
                "Submit Activity",
                type="primary",
            )
        )

    if submit_response:

        errors: list[str] = []

        if not student_id.strip():

            errors.append(
                "Enter your Student ID / "
                "Participant Code."
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
                "Enter your written pedagogical "
                "response."
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

        else:

            submission_reference = make_reference(
                student_id.strip(),
                task_id,
            )

            submission = {
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
                datetime.now().strftime(
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
                "message": (
                    "Your activity has been "
                    "submitted successfully."
                ),
                "reference": submission_reference,
            }

            st.session_state.activity_form_version += 1

            st.rerun()


# =======================================================
# Review responses
# =======================================================

elif page == "Review Responses":

    st.title(
        "Review Responses"
    )

    if not st.session_state.submissions:

        st.warning(
            "No responses have been submitted "
            "in the current session."
        )

    else:

        selected_submission = response_selector(
            "Select a response",
            "review_reference",
        )

        if selected_submission:

            st.divider()

            detail_col1, detail_col2, detail_col3 = (
                st.columns(3)
            )

            detail_col1.metric(
                "Participant Code",
                selected_submission["student_id"],
            )

            detail_col2.metric(
                "Task",
                selected_submission["task_id"],
            )

            detail_col3.metric(
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

            st.markdown(
                "### Pedagogical Prompt"
            )

            st.info(
                selected_submission["prompt"]
            )

            st.markdown(
                "### Voice Reasoning"
            )

            st.audio(
                selected_submission["audio_bytes"],
                format=selected_submission.get(
                    "audio_mime_type",
                    "audio/wav",
                ),
            )

            st.download_button(
                "Download this audio recording",
                selected_submission["audio_bytes"],
                file_name=selected_submission.get(
                    "audio_file_name",
                    "voice_response.wav",
                ),
                mime=selected_submission.get(
                    "audio_mime_type",
                    "audio/wav",
                ),
            )

            st.markdown(
                "### Written Pedagogical Response"
            )

            st.write(
                selected_submission[
                    "written_response"
                ]
            )

            st.markdown(
                "### Reflection: Identified Issue"
            )

            st.write(
                selected_submission[
                    "reflection_issue"
                ]
            )

            st.markdown(
                "### Reflection: Proposed Strategy"
            )

            st.write(
                selected_submission[
                    "reflection_strategy"
                ]
            )

            if selected_submission.get(
                "scores"
            ):

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
                            ][rubric_key]
                            for rubric_key, _ in RUBRIC
                        ],
                    }
                )

                st.dataframe(
                    score_dataframe,
                    hide_index=True,
                    use_container_width=True,
                )

                score_col1, score_col2 = (
                    st.columns(2)
                )

                score_col1.metric(
                    "Total Score",
                    (
                        f'{selected_submission["total_score"]}'
                        f'/{MAX_SCORE}'
                    ),
                )

                score_col2.metric(
                    "Percentage",
                    (
                        f'{selected_submission["percentage"]'
                        f':.2f}%'
                    ),
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
# Score responses
# =======================================================

elif page == "Score Responses":

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

    else:

        selected_submission = response_selector(
            "Select a response to score",
            "score_reference",
        )

        if selected_submission:

            st.markdown(
                "### Pedagogical Prompt"
            )

            st.info(
                selected_submission["prompt"]
            )

            with st.expander(
                "Review participant response before scoring",
                expanded=True,
            ):

                st.markdown(
                    "**Voice Reasoning**"
                )

                st.audio(
                    selected_submission["audio_bytes"],
                    format=selected_submission.get(
                        "audio_mime_type",
                        "audio/wav",
                    ),
                )

                st.markdown(
                    "**Written Pedagogical Response**"
                )

                st.write(
                    selected_submission[
                        "written_response"
                    ]
                )

                st.markdown(
                    "**Reflection: Identified Issue**"
                )

                st.write(
                    selected_submission[
                        "reflection_issue"
                    ]
                )

                st.markdown(
                    "**Reflection: Proposed Strategy**"
                )

                st.write(
                    selected_submission[
                        "reflection_strategy"
                    ]
                )

            st.markdown(
                "### Rubric Scoring"
            )

            st.caption(
                "1 = Very weak, 2 = Weak, "
                "3 = Satisfactory, 4 = Good, "
                "5 = Excellent."
            )

            existing_scores = (
                selected_submission.get(
                    "scores",
                    {},
                )
            )

            score_version = (
                st.session_state.score_form_version
            )

            score_form_key = (
                f'score_form_'
                f'{selected_submission["submission_reference"]}_'
                f'{score_version}'
            )

            with st.form(
                score_form_key
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
                                f'score_'
                                f'{selected_submission["submission_reference"]}_'
                                f'{rubric_key}_'
                                f'{score_version}'
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

                metric_col1, metric_col2 = (
                    st.columns(2)
                )

                metric_col1.metric(
                    "Calculated Total",
                    (
                        f"{calculated_total}"
                        f"/{MAX_SCORE}"
                    ),
                )

                metric_col2.metric(
                    "Calculated Percentage",
                    (
                        f"{calculated_percentage:.2f}%"
                    ),
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
                        f'feedback_'
                        f'{selected_submission["submission_reference"]}_'
                        f'{score_version}'
                    ),
                )

                save_scores = (
                    st.form_submit_button(
                        "Save Scores and Feedback",
                        type="primary",
                    )
                )

            if save_scores:

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
                ] = datetime.now().strftime(
                    "%d-%m-%Y %I:%M %p"
                )

                st.session_state.score_flash = (
                    f'Scores saved for '
                    f'{selected_submission["student_id"]} '
                    f'- '
                    f'{selected_submission["task_id"]}.'
                )

                st.session_state.score_form_version += 1

                st.rerun()


# =======================================================
# Diagnostic profile
# =======================================================

elif page == "Diagnostic Profile":

    st.title(
        "Diagnostic Profile"
    )

    scored_submissions = [
        submission
        for submission in st.session_state.submissions
        if submission.get("scores")
    ]

    if not scored_submissions:

        st.warning(
            "No scored responses are available "
            "in the current session."
        )

    else:

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

        profile_col1, profile_col2, profile_col3 = (
            st.columns(3)
        )

        profile_col1.metric(
            "Name",
            participant_submissions[0]["name"],
        )

        profile_col2.metric(
            "Semester",
            participant_submissions[0]["semester"],
        )

        profile_col3.metric(
            "Scored Tasks",
            len(participant_submissions),
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
                / len(participant_submissions)
            )
            for rubric_key, _ in RUBRIC
        }

        average_percentage = (
            sum(
                submission["percentage"]
                for submission
                in participant_submissions
            )
            / len(participant_submissions)
        )

        strongest_dimension = max(
            dimension_means,
            key=dimension_means.get,
        )

        weakest_dimension = min(
            dimension_means,
            key=dimension_means.get,
        )

        summary_col1, summary_col2, summary_col3 = (
            st.columns(3)
        )

        summary_col1.metric(
            "Average Percentage",
            f"{average_percentage:.2f}%",
        )

        summary_col2.metric(
            "Strongest Area",
            RUBRIC_LABELS[
                strongest_dimension
            ],
        )

        summary_col3.metric(
            "Priority Area",
            RUBRIC_LABELS[
                weakest_dimension
            ],
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
                    dimension_means[
                        rubric_key
                    ]
                    for rubric_key, _ in RUBRIC
                ],
            }
        ).set_index(
            "Dimension"
        )

        st.bar_chart(
            profile_dataframe
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
                    submission[
                        "percentage"
                    ],

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
# Task analytics
# =======================================================

elif page == "Task Analytics":

    st.title(
        "Task Analytics"
    )

    scored_submissions = [
        submission
        for submission in st.session_state.submissions
        if submission.get("scores")
    ]

    analytics_col1, analytics_col2, \
        analytics_col3, analytics_col4 = (
            st.columns(4)
        )

    analytics_col1.metric(
        "Participants",
        len(
            {
                submission["student_id"]
                for submission
                in st.session_state.submissions
            }
        ),
    )

    analytics_col2.metric(
        "Submissions",
        len(
            st.session_state.submissions
        ),
    )

    analytics_col3.metric(
        "Scored Responses",
        len(
            scored_submissions
        ),
    )

    mean_percentage = (
        sum(
            submission["percentage"]
            for submission
            in scored_submissions
        )
        / len(scored_submissions)
        if scored_submissions
        else 0.0
    )

    analytics_col4.metric(
        "Mean Percentage",
        f"{mean_percentage:.2f}%",
    )

    if not scored_submissions:

        st.warning(
            "No scored data are available "
            "for analytics."
        )

    else:

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
                    submission["task_id"],

                    "Category":
                    submission[
                        "task_category"
                    ],

                    "Total Score":
                    submission[
                        "total_score"
                    ],

                    "Percentage":
                    submission[
                        "percentage"
                    ],

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

        st.bar_chart(
            subject_summary.set_index(
                "Subject"
            )
        )

        st.dataframe(
            subject_summary,
            hide_index=True,
            use_container_width=True,
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

        st.bar_chart(
            task_summary.set_index(
                "Task"
            )
        )

        st.dataframe(
            task_summary,
            hide_index=True,
            use_container_width=True,
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

        st.dataframe(
            category_summary,
            hide_index=True,
            use_container_width=True,
        )

        st.markdown(
            "### Dimension-Wise Mean Scores"
        )

        dimension_summary = pd.DataFrame(
            {
                "Dimension": [
                    rubric_label
                    for _, rubric_label
                    in RUBRIC
                ],

                "Mean Score": [
                    analytics_dataframe[
                        rubric_label
                    ].mean()
                    for _, rubric_label
                    in RUBRIC
                ],
            }
        ).set_index(
            "Dimension"
        )

        st.bar_chart(
            dimension_summary
        )

        st.markdown(
            "### Complete Scored Dataset"
        )

        st.dataframe(
            analytics_dataframe,
            hide_index=True,
            use_container_width=True,
        )


# =======================================================
# Download data
# =======================================================

elif page == "Download Data":

    st.title(
        "Download Data"
    )

    if not st.session_state.submissions:

        st.warning(
            "No responses are available for download "
            "in the current session."
        )

    else:

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

        st.markdown(
            "### Data Preview"
        )

        st.dataframe(
            preview_dataframe,
            hide_index=True,
            use_container_width=True,
        )