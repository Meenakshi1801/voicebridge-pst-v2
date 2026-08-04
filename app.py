from __future__ import annotations

import csv
import hmac
import os
import re
import tempfile
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from supabase import Client, create_client


# =========================================================
# APP CONFIGURATION
# =========================================================

MIC_ICON = "\U0001F399"
TABLE_NAME = "voicebridge_submissions"
IST = ZoneInfo("Asia/Kolkata")
APP_DIR = Path(__file__).resolve().parent
PROFILE_IMAGE = APP_DIR / "MD_pic.png"

st.set_page_config(
    page_title="VoiceBridge-PST",
    page_icon=MIC_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# TASK BANK
# =========================================================

TASK_BANK: dict[str, list[dict[str, str]]] = {
    "Pedagogy of Mathematics": [
        {
            "id": "MATH-01",
            "category": "Misconception Diagnosis",
            "prompt": (
                "A Class VI student says that a larger denominator means a larger "
                "fraction. How will you respond as a teacher?"
            ),
        },
        {
            "id": "MATH-02",
            "category": "Error Analysis",
            "prompt": (
                "A student solves 3x + 5 = 20 as 3x = 25. How will you identify "
                "and address this error?"
            ),
        },
        {
            "id": "MATH-03",
            "category": "Concept Explanation",
            "prompt": (
                "How would you explain the difference between area and perimeter "
                "to Class VII students?"
            ),
        },
    ],
    "Pedagogy of Science": [
        {
            "id": "SCI-01",
            "category": "Misconception Diagnosis",
            "prompt": (
                "A Class VII student says that heat and temperature are the same. "
                "How will you respond as a teacher?"
            ),
        },
        {
            "id": "SCI-02",
            "category": "Concept Explanation",
            "prompt": (
                "How would you introduce evaporation through a familiar daily-life "
                "situation?"
            ),
        },
        {
            "id": "SCI-03",
            "category": "Activity Design",
            "prompt": (
                "Suggest a short classroom activity to demonstrate that air occupies "
                "space."
            ),
        },
    ],
    "Pedagogy of Social Science": [
        {
            "id": "SOC-01",
            "category": "Misconception Diagnosis",
            "prompt": (
                "A Class VIII student says that democracy only means voting. How "
                "will you respond as a teacher?"
            ),
        },
        {
            "id": "SOC-02",
            "category": "Concept Explanation",
            "prompt": (
                "How would you explain equality and equity through a classroom or "
                "community example?"
            ),
        },
        {
            "id": "SOC-03",
            "category": "Classroom Engagement",
            "prompt": (
                "Students find history dates boring and disconnected from life. "
                "What teaching strategy will you use?"
            ),
        },
    ],
    "Pedagogy of English": [
        {
            "id": "ENG-01",
            "category": "Learner Support",
            "prompt": (
                "A student can read a passage aloud but cannot infer its meaning. "
                "How will you support the learner?"
            ),
        },
        {
            "id": "ENG-02",
            "category": "Classroom Engagement",
            "prompt": (
                "Students hesitate to speak in English during class. What will you do?"
            ),
        },
        {
            "id": "ENG-03",
            "category": "Assessment Decision",
            "prompt": (
                "After teaching a poem, how would you assess comprehension beyond "
                "memorisation?"
            ),
        },
    ],
    "Pedagogy of Hindi": [
        {
            "id": "HIN-01",
            "category": "Misconception Diagnosis",
            "prompt": (
                "A student memorises a poem but cannot explain its meaning. How will "
                "you respond?"
            ),
        },
        {
            "id": "HIN-02",
            "category": "Concept Explanation",
            "prompt": (
                "How would you introduce idioms through familiar daily-life situations?"
            ),
        },
        {
            "id": "HIN-03",
            "category": "Classroom Engagement",
            "prompt": (
                "Students are reluctant to read a Hindi passage aloud. What will you do?"
            ),
        },
    ],
    "Pedagogy of Commerce": [
        {
            "id": "COM-01",
            "category": "Misconception Diagnosis",
            "prompt": (
                "A student says that sales and profit are the same. How will you respond?"
            ),
        },
        {
            "id": "COM-02",
            "category": "Concept Explanation",
            "prompt": (
                "How would you explain assets and liabilities using examples from "
                "daily life?"
            ),
        },
        {
            "id": "COM-03",
            "category": "Classroom Engagement",
            "prompt": (
                "Students find accounting rules mechanical and boring. What teaching "
                "strategy will you use?"
            ),
        },
    ],
    "Pedagogy of Computer Science": [
        {
            "id": "CS-01",
            "category": "Misconception Diagnosis",
            "prompt": (
                "A student says that the internet and the web are the same. How will "
                "you respond?"
            ),
        },
        {
            "id": "CS-02",
            "category": "Concept Explanation",
            "prompt": (
                "How would you explain an algorithm using a familiar daily-life example?"
            ),
        },
        {
            "id": "CS-03",
            "category": "Inclusive Adaptation",
            "prompt": (
                "How would you support a learner who has limited access to a computer "
                "outside the classroom?"
            ),
        },
    ],
}


# =========================================================
# RUBRIC
# =========================================================

RUBRIC: list[tuple[str, str]] = [
    ("conceptual_clarity", "Conceptual Clarity"),
    ("pedagogical_reasoning", "Pedagogical Reasoning"),
    ("learner_centred_explanation", "Learner-Centred Explanation"),
    ("misconception_diagnosis", "Misconception Diagnosis"),
    ("use_of_example_strategy", "Use of Example / Teaching Strategy"),
    ("reflective_thinking", "Reflective Thinking"),
    ("voice_written_alignment", "Voice-Written Alignment"),
]

RUBRIC_LABELS = dict(RUBRIC)
MAX_SCORE = len(RUBRIC) * 5

MIME_EXTENSIONS = {
    "audio/webm": ".webm",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
}


# =========================================================
# SESSION STATE
# =========================================================

if "teacher_authenticated" not in st.session_state:
    st.session_state.teacher_authenticated = False

if "activity_form_version" not in st.session_state:
    st.session_state.activity_form_version = 0

if "score_form_version" not in st.session_state:
    st.session_state.score_form_version = 0


# =========================================================
# SUPABASE CONNECTION
# =========================================================

def get_secret_value(
    section: str,
    key: str,
    default: str = "",
) -> str:
    try:
        return str(st.secrets[section][key]).strip()
    except (KeyError, TypeError, AttributeError):
        return default


SUPABASE_URL = get_secret_value("supabase", "url")
SUPABASE_SECRET_KEY = get_secret_value("supabase", "secret_key")
BUCKET_NAME = get_secret_value(
    "supabase",
    "bucket",
    "voice-recordings",
)
TEACHER_PASSWORD = get_secret_value("teacher", "password")


@st.cache_resource(show_spinner=False)
def get_supabase_client(
    url: str,
    secret_key: str,
) -> Client:
    return create_client(url, secret_key)


def secrets_are_configured() -> bool:
    return bool(
        SUPABASE_URL.startswith("https://")
        and SUPABASE_URL.endswith(".supabase.co")
        and SUPABASE_SECRET_KEY
        and BUCKET_NAME
    )


def supabase_client() -> Client:
    if not secrets_are_configured():
        raise RuntimeError(
            "Supabase secrets are incomplete or invalid."
        )

    return get_supabase_client(
        SUPABASE_URL,
        SUPABASE_SECRET_KEY,
    )


@st.cache_data(ttl=60, show_spinner=False)
def storage_connection_status() -> tuple[bool, str]:
    if not secrets_are_configured():
        return (
            False,
            "Supabase secrets are incomplete or invalid.",
        )

    try:
        client = supabase_client()

        client.table(TABLE_NAME).select(
            "id"
        ).limit(1).execute()

        client.storage.get_bucket(BUCKET_NAME)

        return True, ""

    except Exception as exc:
        return False, str(exc)


# =========================================================
# DATABASE AND STORAGE HELPERS
# =========================================================

def now_ist() -> datetime:
    return datetime.now(IST)


def safe_identifier(
    value: str,
    fallback: str = "participant",
) -> str:
    cleaned = re.sub(
        r"[^A-Za-z0-9_-]+",
        "-",
        value.strip(),
    ).strip("-")

    return cleaned or fallback


def make_reference(
    student_id: str,
    task_id: str,
) -> str:
    timestamp = now_ist().strftime(
        "%Y%m%d%H%M%S%f"
    )

    return (
        f"{safe_identifier(student_id).upper()}-"
        f"{task_id}-"
        f"{timestamp}"
    )


def normalise_audio_mime(
    mime_type: str | None,
) -> str:
    mime = (
        mime_type or "audio/wav"
    ).lower().strip()

    if mime == "audio/x-wav":
        return "audio/wav"

    allowed_types = {
        "audio/webm",
        "audio/wav",
        "audio/mpeg",
        "audio/mp4",
    }

    if mime not in allowed_types:
        return "audio/wav"

    return mime


def upload_audio_recording(
    audio_bytes: bytes,
    storage_path: str,
    mime_type: str,
) -> None:
    """
    Save the recording temporarily and pass an opened
    binary file to Supabase Storage.

    This avoids passing BytesIO directly to the Storage
    client, which caused the earlier submission error.
    """

    extension = MIME_EXTENSIONS.get(
        mime_type,
        ".wav",
    )

    temporary_path: str | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            suffix=extension,
            delete=False,
        ) as temporary_file:

            temporary_file.write(audio_bytes)
            temporary_path = temporary_file.name

        with open(
            temporary_path,
            "rb",
        ) as binary_file:

            (
                supabase_client()
                .storage
                .from_(BUCKET_NAME)
                .upload(
                    path=storage_path,
                    file=binary_file,
                    file_options={
                        "content-type": mime_type,
                        "cache-control": "3600",
                        "upsert": "false",
                    },
                )
            )

    finally:
        if (
            temporary_path
            and os.path.exists(temporary_path)
        ):
            os.remove(temporary_path)


def delete_audio_recording(
    storage_path: str,
) -> None:
    try:
        (
            supabase_client()
            .storage
            .from_(BUCKET_NAME)
            .remove([storage_path])
        )

    except Exception:
        pass


@st.cache_data(ttl=20, show_spinner=False)
def fetch_all_submissions() -> list[dict[str, Any]]:
    client = supabase_client()

    rows: list[dict[str, Any]] = []

    page_size = 1000
    start = 0

    while True:
        response = (
            client.table(TABLE_NAME)
            .select("*")
            .order(
                "submitted_at",
                desc=True,
            )
            .range(
                start,
                start + page_size - 1,
            )
            .execute()
        )

        batch = response.data or []
        rows.extend(batch)

        if len(batch) < page_size:
            break

        start += page_size

    return rows


@st.cache_data(ttl=300, show_spinner=False)
def download_audio_recording(
    storage_path: str,
) -> bytes:
    return (
        supabase_client()
        .storage
        .from_(BUCKET_NAME)
        .download(storage_path)
    )


def insert_submission(
    record: dict[str, Any],
) -> None:
    (
        supabase_client()
        .table(TABLE_NAME)
        .insert(record)
        .execute()
    )

    fetch_all_submissions.clear()


def update_submission_scores(
    reference: str,
    values: dict[str, Any],
) -> None:
    (
        supabase_client()
        .table(TABLE_NAME)
        .update(values)
        .eq(
            "submission_reference",
            reference,
        )
        .execute()
    )

    fetch_all_submissions.clear()


def is_scored(
    submission: dict[str, Any],
) -> bool:
    return submission.get(
        "total_score"
    ) is not None


def format_database_time(
    value: Any,
) -> str:
    if not value:
        return ""

    try:
        timestamp = pd.to_datetime(
            value,
            utc=True,
        )

        timestamp = timestamp.tz_convert(
            "Asia/Kolkata"
        )

        return timestamp.strftime(
            "%d-%m-%Y %I:%M %p"
        )

    except Exception:
        return str(value)


def response_label(
    submission: dict[str, Any],
) -> str:
    submitted = format_database_time(
        submission.get("submitted_at")
    )

    return (
        f'{submission.get("student_id", "")} | '
        f'{submission.get("task_id", "")} | '
        f'{submission.get("participant_name", "")} | '
        f"{submitted}"
    )


def response_selector(
    label: str,
    key: str,
    submissions: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not submissions:
        return None

    references = [
        row["submission_reference"]
        for row in submissions
    ]

    labels = {
        row["submission_reference"]:
        response_label(row)
        for row in submissions
    }

    selected_reference = st.selectbox(
        label,
        references,
        format_func=lambda reference: labels.get(
            reference,
            reference,
        ),
        key=key,
    )

    return next(
        (
            row
            for row in submissions
            if row["submission_reference"]
            == selected_reference
        ),
        None,
    )


def generate_feedback(
    scores: dict[str, int],
) -> str:
    strongest_key = max(
        scores,
        key=scores.get,
    )

    priority_key = min(
        scores,
        key=scores.get,
    )

    suggestions = {
        "conceptual_clarity": (
            "Clarify the central concept and use precise "
            "subject terminology."
        ),
        "pedagogical_reasoning": (
            "Explain why the proposed response is "
            "appropriate for this learner."
        ),
        "learner_centred_explanation": (
            "Connect the explanation more explicitly "
            "with learners' prior knowledge and needs."
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
            "Include deeper reflection on limitations, "
            "alternatives, and improvement."
        ),
        "voice_written_alignment": (
            "Improve consistency between the oral "
            "reasoning and written response."
        ),
    }

    return (
        f"Strongest area: "
        f"{RUBRIC_LABELS[strongest_key]}. "
        f"Priority area: "
        f"{RUBRIC_LABELS[priority_key]}. "
        f"Suggested action: "
        f"{suggestions[priority_key]}"
    )


def show_response_content(
    submission: dict[str, Any],
) -> None:
    st.markdown(
        "### Pedagogical Prompt"
    )

    st.info(
        submission.get("prompt", "")
    )

    st.markdown(
        "### Voice Reasoning"
    )

    storage_path = submission.get(
        "audio_path",
        "",
    )

    if storage_path:
        try:
            audio_bytes = download_audio_recording(
                storage_path
            )

            mime_type = (
                submission.get("audio_mime_type")
                or "audio/wav"
            )

            st.audio(
                audio_bytes,
                format=mime_type,
            )

            st.download_button(
                "Download this audio recording",
                data=audio_bytes,
                file_name=(
                    submission.get(
                        "audio_file_name"
                    )
                    or Path(storage_path).name
                ),
                mime=mime_type,
                key=(
                    "audio_download_"
                    f'{submission.get("submission_reference", "")}'
                ),
            )

        except Exception as exc:
            st.error(
                "The audio recording could not be "
                "retrieved from private storage."
            )

            st.caption(
                str(exc)[:300]
            )

    else:
        st.warning(
            "No audio path is stored for this response."
        )

    st.markdown(
        "### Written Pedagogical Response"
    )

    st.write(
        submission.get(
            "written_response",
            "",
        )
    )

    st.markdown(
        "### Reflection: Identified Issue"
    )

    st.write(
        submission.get(
            "reflection_issue",
            "",
        )
    )

    st.markdown(
        "### Reflection: Proposed Strategy"
    )

    st.write(
        submission.get(
            "reflection_strategy",
            "",
        )
    )


# =========================================================
# PAGE: HOME
# =========================================================

def render_home() -> None:
    st.markdown(
        f"# {MIC_ICON} VoiceBridge-PST Dashboard"
    )

    st.subheader(
        "Voice-First Micro-Pedagogical Reasoning "
        "Activity and Analytics Platform"
    )

    st.write("")

    photograph_column, information_column = (
        st.columns(
            [1, 2.6],
            gap="large",
        )
    )

    with photograph_column:
        if PROFILE_IMAGE.exists():
            st.image(
                str(PROFILE_IMAGE),
                width=210,
            )

        else:
            st.warning(
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
            "Department of Education / "
            "School of Education  \n"
            "Mahatma Jyotiba Phule Rohilkhand "
            "University  \n"
            "Bareilly, Uttar Pradesh, India"
        )

    st.divider()

    st.header(
        "Purpose"
    )

    st.write(
        "VoiceBridge-PST is a voice-first activity "
        "and analytics platform designed to support "
        "the assessment and development of "
        "micro-pedagogical reasoning among "
        "pre-service teachers."
    )

    st.header(
        "Activity Flow"
    )

    st.write(
        "Pedagogical Prompt → Voice Reasoning → "
        "Written Pedagogical Response → "
        "Reflective Response → "
        "Teacher-Educator Review → "
        "Rubric Scoring → Diagnostic Feedback"
    )

    st.header(
        "Permanent and Private Storage"
    )

    st.write(
        "Participant details, written responses, "
        "rubric scores, and feedback are stored in "
        "the VoiceBridge-PST database. Voice "
        "recordings are stored in the private "
        "voice-recordings bucket. Teacher-Educator "
        "pages require the private password."
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


# =========================================================
# PAGE: ACTIVITY SUBMISSION
# =========================================================

def render_activity_submission() -> None:
    st.title(
        "Activity Submission"
    )

    connected, connection_error = (
        storage_connection_status()
    )

    if not connected:
        st.error(
            "The permanent storage connection "
            "is not available."
        )

        if connection_error:
            st.caption(
                connection_error[:300]
            )

        return

    if "submission_flash" in st.session_state:
        flash = st.session_state.pop(
            "submission_flash"
        )

        st.success(
            "Your activity has been submitted "
            "successfully."
        )

        st.info(
            "Submission reference: "
            f'{flash["reference"]}'
        )

    st.write(
        "Select your pedagogy subject and task. "
        "Record your voice reasoning and complete "
        "the written and reflective responses."
    )

    selected_subject = st.selectbox(
        "Pedagogy Subject",
        list(TASK_BANK.keys()),
        key="selected_subject",
    )

    tasks = TASK_BANK[selected_subject]

    task_labels = [
        f'{task["id"]} - {task["category"]}'
        for task in tasks
    ]

    selected_task_label = st.selectbox(
        "Task",
        task_labels,
        key=f"selected_task_{selected_subject}",
    )

    selected_task = tasks[
        task_labels.index(
            selected_task_label
        )
    ]

    task_id = selected_task["id"]
    task_category = selected_task["category"]
    prompt = selected_task["prompt"]

    st.markdown(
        "### Pedagogical Prompt"
    )

    st.info(prompt)

    task_column_1, task_column_2 = (
        st.columns(2)
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
        "Suggested duration: 2–3 minutes. "
        "Allow microphone access when requested."
    )

    version = (
        st.session_state.activity_form_version
    )

    audio_response = st.audio_input(
        "Record your voice response",
        key=f"audio_{task_id}_{version}",
    )

    if audio_response is not None:
        st.success(
            "Voice response recorded successfully."
        )

        st.audio(audio_response)

    st.divider()

    with st.form(
        f"activity_form_{version}"
    ):
        st.markdown(
            "## Participant Details"
        )

        (
            participant_column_1,
            participant_column_2,
        ) = st.columns(2)

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
            "150–200 words."
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

        submitted = st.form_submit_button(
            "Submit Activity",
            type="primary",
        )

    if not submitted:
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

    reference = make_reference(
        student_id,
        task_id,
    )

    mime_type = normalise_audio_mime(
        getattr(
            audio_response,
            "type",
            None,
        )
    )

    extension = MIME_EXTENSIONS.get(
        mime_type,
        ".wav",
    )

    storage_path = (
        f"{safe_identifier(student_id).upper()}/"
        f"{reference}{extension}"
    )

    audio_file_name = (
        f"{reference}{extension}"
    )

    audio_bytes = (
        audio_response.getvalue()
    )

    try:
        with st.spinner(
            "Saving the voice recording and "
            "response securely..."
        ):
            upload_audio_recording(
                audio_bytes=audio_bytes,
                storage_path=storage_path,
                mime_type=mime_type,
            )

            database_record = {
                "submission_reference":
                reference,

                "student_id":
                student_id.strip(),

                "participant_name":
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

                "audio_path":
                storage_path,

                "audio_file_name":
                audio_file_name,

                "audio_mime_type":
                mime_type,

                "written_response":
                written_response.strip(),

                "reflection_issue":
                reflection_issue.strip(),

                "reflection_strategy":
                reflection_strategy.strip(),
            }

            try:
                insert_submission(
                    database_record
                )

            except Exception:
                delete_audio_recording(
                    storage_path
                )

                raise

        st.session_state.submission_flash = {
            "reference": reference
        }

        st.session_state.activity_form_version += 1

        st.rerun()

    except Exception as exc:
        st.error(
            "The submission could not be saved. "
            "Your form has not been cleared. "
            "Please try again."
        )

        st.caption(
            str(exc)[:500]
        )


# =========================================================
# PAGE: TEACHER LOGIN
# =========================================================

def render_teacher_login() -> None:
    st.title(
        "Teacher-Educator Access"
    )

    connected, connection_error = (
        storage_connection_status()
    )

    if not connected:
        st.error(
            "The permanent storage connection "
            "is not available."
        )

        if connection_error:
            st.caption(
                connection_error[:300]
            )

        return

    if not TEACHER_PASSWORD:
        st.error(
            "The Teacher-Educator password "
            "has not been configured."
        )

        return

    if st.session_state.teacher_authenticated:
        st.success(
            "Teacher-Educator access is active."
        )

        st.write(
            "Use the private pages now shown in the "
            "sidebar to review, score, analyse, and "
            "download submissions."
        )

        if st.button(
            "Log out",
            type="secondary",
        ):
            st.session_state.teacher_authenticated = False

            st.rerun()

        return

    with st.form(
        "teacher_login_form"
    ):
        entered_password = st.text_input(
            "Private Teacher-Educator Password",
            type="password",
        )

        login_clicked = st.form_submit_button(
            "Log in",
            type="primary",
        )

    if login_clicked:
        if hmac.compare_digest(
            entered_password,
            TEACHER_PASSWORD,
        ):
            st.session_state.teacher_authenticated = True

            st.success(
                "Login successful."
            )

            st.rerun()

        else:
            st.error(
                "The password is incorrect."
            )


# =========================================================
# TEACHER PAGE GUARD
# =========================================================

def require_teacher_access() -> bool:
    if not st.session_state.teacher_authenticated:
        st.warning(
            "Log in through Teacher-Educator Login "
            "to open this page."
        )

        return False

    return True


# =========================================================
# PAGE: REVIEW RESPONSES
# =========================================================

def render_review_responses() -> None:
    st.title(
        "Review Responses"
    )

    if not require_teacher_access():
        return

    try:
        submissions = fetch_all_submissions()

    except Exception as exc:
        st.error(
            "Submissions could not be retrieved "
            "from the database."
        )

        st.caption(
            str(exc)[:300]
        )

        return

    if not submissions:
        st.warning(
            "No responses have been submitted."
        )

        return

    selected = response_selector(
        "Select a response",
        "review_reference",
        submissions,
    )

    if selected is None:
        return

    st.divider()

    column_1, column_2, column_3 = (
        st.columns(3)
    )

    column_1.metric(
        "Participant Code",
        selected.get(
            "student_id",
            "",
        ),
    )

    column_2.metric(
        "Task",
        selected.get(
            "task_id",
            "",
        ),
    )

    column_3.metric(
        "Semester",
        selected.get(
            "semester",
            "",
        ),
    )

    st.markdown(
        "### Participant Information"
    )

    st.write(
        f'**Name:** '
        f'{selected.get("participant_name", "")}'
    )

    st.write(
        f'**Pedagogy Subject:** '
        f'{selected.get("pedagogy_subject", "")}'
    )

    st.write(
        f'**Task Category:** '
        f'{selected.get("task_category", "")}'
    )

    st.write(
        "**Submission Time:** "
        f'{format_database_time(selected.get("submitted_at"))}'
    )

    st.write(
        f'**Reference:** '
        f'{selected.get("submission_reference", "")}'
    )

    show_response_content(
        selected
    )

    if is_scored(selected):
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
                    selected.get(key)
                    for key, _ in RUBRIC
                ],
            }
        )

        st.dataframe(
            score_dataframe,
            hide_index=True,
            use_container_width=True,
        )

        (
            score_column_1,
            score_column_2,
        ) = st.columns(2)

        score_column_1.metric(
            "Total Score",
            f'{selected.get("total_score", 0)}'
            f"/{MAX_SCORE}",
        )

        score_column_2.metric(
            "Percentage",
            f'{float(selected.get("percentage") or 0):.2f}%',
        )

        st.markdown(
            "### Teacher-Educator Feedback"
        )

        st.info(
            selected.get("teacher_feedback")
            or "No feedback was entered."
        )


# =========================================================
# PAGE: SCORE RESPONSES
# =========================================================

def render_score_responses() -> None:
    st.title(
        "Score Responses"
    )

    if not require_teacher_access():
        return

    if "score_flash" in st.session_state:
        st.success(
            st.session_state.pop(
                "score_flash"
            )
        )

    try:
        submissions = fetch_all_submissions()

    except Exception as exc:
        st.error(
            "Submissions could not be retrieved "
            "from the database."
        )

        st.caption(
            str(exc)[:300]
        )

        return

    if not submissions:
        st.warning(
            "No responses are available for scoring."
        )

        return

    selected = response_selector(
        "Select a response to score",
        "score_reference",
        submissions,
    )

    if selected is None:
        return

    with st.expander(
        "Review participant response before scoring",
        expanded=True,
    ):
        show_response_content(
            selected
        )

    st.markdown(
        "### Rubric Scoring"
    )

    st.caption(
        "1 = Very weak, 2 = Weak, "
        "3 = Satisfactory, 4 = Good, "
        "5 = Excellent."
    )

    version = (
        st.session_state.score_form_version
    )

    reference = selected[
        "submission_reference"
    ]

    with st.form(
        f"score_form_{reference}_{version}"
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

            saved_value = selected.get(
                rubric_key
            )

            default_value = (
                int(saved_value)
                if saved_value is not None
                else 3
            )

            with target_column:
                entered_scores[rubric_key] = st.slider(
                    rubric_label,
                    min_value=1,
                    max_value=5,
                    value=default_value,
                    step=1,
                    key=(
                        f"score_{reference}_"
                        f"{rubric_key}_{version}"
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

        (
            metric_column_1,
            metric_column_2,
        ) = st.columns(2)

        metric_column_1.metric(
            "Calculated Total",
            f"{calculated_total}/{MAX_SCORE}",
        )

        metric_column_2.metric(
            "Calculated Percentage",
            f"{calculated_percentage:.2f}%",
        )

        teacher_feedback = st.text_area(
            "Teacher-Educator Feedback",
            value=(
                selected.get("teacher_feedback")
                or ""
            ),
            height=140,
            placeholder=(
                "Leave blank to use automatically "
                "generated diagnostic feedback."
            ),
            key=(
                f"feedback_{reference}_{version}"
            ),
        )

        save_clicked = st.form_submit_button(
            "Save Scores and Feedback",
            type="primary",
        )

    if not save_clicked:
        return

    update_values: dict[str, Any] = {
        **entered_scores,

        "total_score":
        calculated_total,

        "percentage":
        round(
            calculated_percentage,
            2,
        ),

        "teacher_feedback":
        (
            teacher_feedback.strip()
            or generate_feedback(
                entered_scores
            )
        ),

        "scored_at":
        now_ist().isoformat(),
    }

    try:
        with st.spinner(
            "Saving scores and feedback..."
        ):
            update_submission_scores(
                reference,
                update_values,
            )

        st.session_state.score_flash = (
            f'Scores saved for '
            f'{selected.get("student_id", "")} - '
            f'{selected.get("task_id", "")}.'
        )

        st.session_state.score_form_version += 1

        st.rerun()

    except Exception as exc:
        st.error(
            "Scores and feedback could not be saved."
        )

        st.caption(
            str(exc)[:500]
        )


# =========================================================
# PAGE: DIAGNOSTIC PROFILE
# =========================================================

def render_diagnostic_profile() -> None:
    st.title(
        "Diagnostic Profile"
    )

    if not require_teacher_access():
        return

    try:
        submissions = fetch_all_submissions()

    except Exception as exc:
        st.error(
            "Data could not be retrieved "
            "from the database."
        )

        st.caption(
            str(exc)[:300]
        )

        return

    scored = [
        row
        for row in submissions
        if is_scored(row)
    ]

    if not scored:
        st.warning(
            "No scored responses are available."
        )

        return

    participant_ids = sorted(
        {
            row["student_id"]
            for row in scored
        }
    )

    selected_student_id = st.selectbox(
        "Select Participant Code",
        participant_ids,
    )

    participant_rows = [
        row
        for row in scored
        if row["student_id"]
        == selected_student_id
    ]

    st.subheader(
        f"Diagnostic Profile: "
        f"{selected_student_id}"
    )

    (
        profile_column_1,
        profile_column_2,
        profile_column_3,
    ) = st.columns(3)

    profile_column_1.metric(
        "Name",
        participant_rows[0].get(
            "participant_name",
            "",
        ),
    )

    profile_column_2.metric(
        "Semester",
        participant_rows[0].get(
            "semester",
            "",
        ),
    )

    profile_column_3.metric(
        "Scored Tasks",
        len(participant_rows),
    )

    dimension_means: dict[str, float] = {}

    for rubric_key, _ in RUBRIC:
        values = [
            float(row[rubric_key])
            for row in participant_rows
            if row.get(rubric_key)
            is not None
        ]

        dimension_means[rubric_key] = (
            sum(values) / len(values)
            if values
            else 0.0
        )

    percentages = [
        float(
            row.get("percentage") or 0
        )
        for row in participant_rows
    ]

    average_percentage = (
        sum(percentages)
        / len(percentages)
    )

    strongest_key = max(
        dimension_means,
        key=dimension_means.get,
    )

    priority_key = min(
        dimension_means,
        key=dimension_means.get,
    )

    (
        summary_column_1,
        summary_column_2,
        summary_column_3,
    ) = st.columns(
        [1, 1.4, 1.4]
    )

    summary_column_1.metric(
        "Average Percentage",
        f"{average_percentage:.2f}%",
    )

    with summary_column_2:
        st.caption(
            "Strongest Area"
        )

        st.success(
            RUBRIC_LABELS[
                strongest_key
            ]
        )

    with summary_column_3:
        st.caption(
            "Priority Area"
        )

        st.warning(
            RUBRIC_LABELS[
                priority_key
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
                    dimension_means[key],
                    2,
                )
                for key, _ in RUBRIC
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
                row.get(
                    "task_id",
                    "",
                ),

                "Subject":
                row.get(
                    "pedagogy_subject",
                    "",
                ),

                "Total Score":
                row.get(
                    "total_score"
                ),

                "Percentage":
                round(
                    float(
                        row.get(
                            "percentage"
                        )
                        or 0
                    ),
                    2,
                ),

                "Scored Time":
                format_database_time(
                    row.get("scored_at")
                ),
            }

            for row in participant_rows
        ]
    )

    st.dataframe(
        task_dataframe,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Percentage":
            st.column_config.NumberColumn(
                "Percentage (%)",
                format="%.2f",
            )
        },
    )

    latest_feedback = next(
        (
            row.get("teacher_feedback")
            for row in participant_rows
            if row.get("teacher_feedback")
        ),
        "No feedback is available.",
    )

    st.markdown(
        "### Latest Diagnostic Feedback"
    )

    st.info(
        latest_feedback
    )


# =========================================================
# PAGE: TASK ANALYTICS
# =========================================================

def render_task_analytics() -> None:
    st.title(
        "Task Analytics"
    )

    if not require_teacher_access():
        return

    try:
        submissions = fetch_all_submissions()

    except Exception as exc:
        st.error(
            "Data could not be retrieved "
            "from the database."
        )

        st.caption(
            str(exc)[:300]
        )

        return

    scored = [
        row
        for row in submissions
        if is_scored(row)
    ]

    (
        metric_1,
        metric_2,
        metric_3,
        metric_4,
    ) = st.columns(4)

    metric_1.metric(
        "Participants",
        len(
            {
                row["student_id"]
                for row in submissions
            }
        ),
    )

    metric_2.metric(
        "Submissions",
        len(submissions),
    )

    metric_3.metric(
        "Scored Responses",
        len(scored),
    )

    mean_percentage = (
        sum(
            float(
                row.get("percentage") or 0
            )
            for row in scored
        )
        / len(scored)
        if scored
        else 0.0
    )

    metric_4.metric(
        "Mean Percentage",
        f"{mean_percentage:.2f}%",
    )

    if not scored:
        st.warning(
            "No scored data are available "
            "for analytics."
        )

        return

    analytics_dataframe = pd.DataFrame(
        [
            {
                "Participant":
                row.get(
                    "student_id",
                    "",
                ),

                "Subject":
                row.get(
                    "pedagogy_subject",
                    "",
                ),

                "Task":
                row.get(
                    "task_id",
                    "",
                ),

                "Category":
                row.get(
                    "task_category",
                    "",
                ),

                "Total Score":
                row.get(
                    "total_score"
                ),

                "Percentage":
                round(
                    float(
                        row.get(
                            "percentage"
                        )
                        or 0
                    ),
                    2,
                ),

                **{
                    rubric_label:
                    row.get(rubric_key)

                    for rubric_key, rubric_label
                    in RUBRIC
                },
            }

            for row in scored
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

    if len(subject_summary) == 1:
        st.metric(
            subject_summary.iloc[0][
                "Subject"
            ],
            (
                f'{subject_summary.iloc[0]["Percentage"]:.2f}%'
            ),
        )

    else:
        st.bar_chart(
            subject_summary,
            x="Percentage",
            y="Subject",
            horizontal=True,
            height=320,
        )

    st.dataframe(
        subject_summary,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Percentage":
            st.column_config.NumberColumn(
                "Mean Percentage (%)",
                format="%.2f",
            )
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
        .sort_values("Task")
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
        height=320,
    )

    st.markdown(
        "### Dimension-Wise Mean Scores"
    )

    dimension_summary = pd.DataFrame(
        {
            "Dimension": [
                label
                for _, label in RUBRIC
            ],

            "Mean Score": [
                round(
                    float(
                        analytics_dataframe[
                            label
                        ].mean()
                    ),
                    2,
                )
                for _, label in RUBRIC
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

    st.dataframe(
        analytics_dataframe[
            [
                "Participant",
                "Subject",
                "Task",
                "Category",
                "Total Score",
                "Percentage",
            ]
        ],
        hide_index=True,
        use_container_width=True,
        column_config={
            "Percentage":
            st.column_config.NumberColumn(
                "Percentage (%)",
                format="%.2f",
            )
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
                )
            },
        )


# =========================================================
# PAGE: DOWNLOAD DATA
# =========================================================

def submissions_to_csv(
    submissions: list[dict[str, Any]],
) -> bytes:
    output = StringIO()

    fields = [
        "submission_reference",
        "student_id",
        "participant_name",
        "semester",
        "pedagogy_subject",
        "task_id",
        "task_category",
        "prompt",
        "audio_path",
        "audio_file_name",
        "audio_mime_type",
        "written_response",
        "reflection_issue",
        "reflection_strategy",
        "submitted_at",
        *[
            key
            for key, _ in RUBRIC
        ],
        "total_score",
        "percentage",
        "teacher_feedback",
        "scored_at",
    ]

    writer = csv.DictWriter(
        output,
        fieldnames=fields,
    )

    writer.writeheader()

    for submission in submissions:
        row = {
            field:
            submission.get(
                field,
                "",
            )
            for field in fields
        }

        if isinstance(
            row.get("percentage"),
            (int, float),
        ):
            row["percentage"] = round(
                float(row["percentage"]),
                2,
            )

        writer.writerow(row)

    return output.getvalue().encode(
        "utf-8-sig"
    )


def render_download_data() -> None:
    st.title(
        "Download Data"
    )

    if not require_teacher_access():
        return

    try:
        submissions = fetch_all_submissions()

    except Exception as exc:
        st.error(
            "Data could not be retrieved "
            "from the database."
        )

        st.caption(
            str(exc)[:300]
        )

        return

    if not submissions:
        st.warning(
            "No responses are available "
            "for download."
        )

        return

    st.download_button(
        "Download Complete Submission Data as CSV",
        data=submissions_to_csv(
            submissions
        ),
        file_name=(
            "VoiceBridge_PST_"
            "Submissions_and_Scores.csv"
        ),
        mime="text/csv",
        type="primary",
    )

    st.caption(
        "The CSV includes participant details, "
        "task information, written responses, "
        "reflections, rubric scores, total score, "
        "percentage, teacher feedback, and "
        "audio-file metadata. Audio recordings "
        "can be downloaded individually from "
        "Review Responses."
    )

    preview_dataframe = pd.DataFrame(
        [
            {
                "Participant":
                row.get(
                    "student_id",
                    "",
                ),

                "Name":
                row.get(
                    "participant_name",
                    "",
                ),

                "Subject":
                row.get(
                    "pedagogy_subject",
                    "",
                ),

                "Task":
                row.get(
                    "task_id",
                    "",
                ),

                "Scored":
                (
                    "Yes"
                    if is_scored(row)
                    else "No"
                ),

                "Total Score":
                row.get(
                    "total_score"
                ),

                "Percentage":
                row.get(
                    "percentage"
                ),

                "Reference":
                row.get(
                    "submission_reference",
                    "",
                ),
            }

            for row in submissions
        ]
    )

    preview_dataframe[
        "Percentage"
    ] = pd.to_numeric(
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
        column_config={
            "Percentage":
            st.column_config.NumberColumn(
                "Percentage (%)",
                format="%.2f",
            )
        },
    )


# =========================================================
# SIDEBAR AND ROUTING
# =========================================================

st.sidebar.markdown(
    f"## {MIC_ICON} VoiceBridge-PST"
)

st.sidebar.caption(
    "Activity and Analytics Platform"
)

public_pages = [
    "Home",
    "Activity Submission",
    "Teacher-Educator Login",
]

teacher_pages = [
    "Review Responses",
    "Score Responses",
    "Diagnostic Profile",
    "Task Analytics",
    "Download Data",
]

navigation_options = public_pages.copy()

if st.session_state.teacher_authenticated:
    navigation_options.extend(
        teacher_pages
    )

page = st.sidebar.radio(
    "Navigation",
    navigation_options,
    key="main_navigation",
)

st.sidebar.divider()

st.sidebar.info(
    "Participants can submit activities. "
    "Teacher-Educator data pages require "
    "the private password."
)

connected, connection_error = (
    storage_connection_status()
)

if connected:
    st.sidebar.success(
        "Permanent cloud storage connected"
    )

else:
    st.sidebar.error(
        "Permanent storage is not connected."
    )

    if connection_error:
        st.sidebar.caption(
            connection_error[:180]
        )

if st.session_state.teacher_authenticated:
    st.sidebar.success(
        "Teacher-Educator access active"
    )

    if st.sidebar.button(
        "Log out",
        key="sidebar_logout",
    ):
        st.session_state.teacher_authenticated = False

        st.rerun()

PAGES = {
    "Home":
    render_home,

    "Activity Submission":
    render_activity_submission,

    "Teacher-Educator Login":
    render_teacher_login,

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