from __future__ import annotations

import csv
import os
import re
import tempfile
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from supabase import Client, create_client


# =======================================================
# PAGE CONFIGURATION
# =======================================================

MIC_ICON = "\U0001F399"
APP_TITLE = "VoiceBridge-PST"
TABLE_NAME = "voicebridge_submissions"
MAX_AUDIO_BYTES = 10 * 1024 * 1024
MAX_SCORE = 35
IST = ZoneInfo("Asia/Kolkata")
APP_DIR = Path(__file__).resolve().parent
PROFILE_IMAGE = APP_DIR / "MD_pic.png"

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=MIC_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


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
    ("conceptual_clarity", "Conceptual Clarity"),
    ("pedagogical_reasoning", "Pedagogical Reasoning"),
    ("learner_centred_explanation", "Learner-Centred Explanation"),
    ("misconception_diagnosis", "Misconception Diagnosis"),
    ("use_of_example_strategy", "Use of Example / Teaching Strategy"),
    ("reflective_thinking", "Reflective Thinking"),
    ("voice_written_alignment", "Voice-Written Alignment"),
]

RUBRIC_LABELS = dict(RUBRIC)
RUBRIC_KEYS = [key for key, _ in RUBRIC]

# =======================================================
# SESSION STATE
# =======================================================

SESSION_DEFAULTS = {
    "auth_access_token": "",
    "auth_refresh_token": "",
    "auth_user_id": "",
    "auth_email": "",
    "activity_form_version": 0,
    "score_form_version": 0,
}

for state_key, default_value in SESSION_DEFAULTS.items():
    if state_key not in st.session_state:
        st.session_state[state_key] = default_value


# =======================================================
# CONFIGURATION AND SUPABASE CONNECTIONS
# =======================================================


def get_app_config() -> dict[str, str]:
    """Read server and public credentials from Streamlit Secrets."""

    try:
        return {
            "supabase_url": str(st.secrets["supabase"]["url"]).strip(),
            "publishable_key": str(
                st.secrets["supabase"]["publishable_key"]
            ).strip(),
            "secret_key": str(st.secrets["supabase"]["secret_key"]).strip(),
            "bucket": str(st.secrets["supabase"]["bucket"]).strip(),
        }
    except (KeyError, FileNotFoundError, TypeError) as exc:
        raise RuntimeError(
            "Streamlit Secrets are incomplete. Add url, publishable_key, "
            "secret_key, and bucket under [supabase]."
        ) from exc


@st.cache_resource(show_spinner=False)
def get_service_client(url: str, secret_key: str) -> Client:
    """Create the trusted server-side client used for public submissions/admin work."""

    return create_client(url, secret_key)


try:
    APP_CONFIG = get_app_config()
    SERVICE = get_service_client(
        APP_CONFIG["supabase_url"],
        APP_CONFIG["secret_key"],
    )
    BUCKET_NAME = APP_CONFIG["bucket"]
    CONFIGURATION_ERROR = ""
except Exception as configuration_exception:
    APP_CONFIG = {}
    SERVICE = None
    BUCKET_NAME = ""
    CONFIGURATION_ERROR = str(configuration_exception)


_RUNTIME_USER_CLIENT: Client | None = None
_RUNTIME_USER: Any = None
_RUNTIME_PROFILE: dict[str, Any] | None = None


def create_public_client() -> Client:
    """Create a per-session client that uses the publishable key."""

    if not APP_CONFIG:
        raise RuntimeError("Supabase is not configured.")

    return create_client(
        APP_CONFIG["supabase_url"],
        APP_CONFIG["publishable_key"],
    )


def clear_auth_state() -> None:
    """Remove the current browser session's login tokens."""

    global _RUNTIME_USER_CLIENT, _RUNTIME_USER, _RUNTIME_PROFILE

    st.session_state.auth_access_token = ""
    st.session_state.auth_refresh_token = ""
    st.session_state.auth_user_id = ""
    st.session_state.auth_email = ""
    _RUNTIME_USER_CLIENT = None
    _RUNTIME_USER = None
    _RUNTIME_PROFILE = None


def store_auth_session(auth_response: Any) -> None:
    """Store access and refresh tokens returned by Supabase Auth."""

    session = getattr(auth_response, "session", None)
    user = getattr(auth_response, "user", None)

    if session is None:
        raise RuntimeError("No authenticated session was returned.")

    st.session_state.auth_access_token = str(session.access_token)
    st.session_state.auth_refresh_token = str(session.refresh_token)

    if user is not None:
        st.session_state.auth_user_id = str(user.id)
        st.session_state.auth_email = str(user.email or "")


def get_user_context() -> tuple[Client, Any, dict[str, Any]]:
    """Restore, verify, and return the logged-in user's authenticated context."""

    global _RUNTIME_USER_CLIENT, _RUNTIME_USER, _RUNTIME_PROFILE

    if (
        _RUNTIME_USER_CLIENT is not None
        and _RUNTIME_USER is not None
        and _RUNTIME_PROFILE is not None
    ):
        return _RUNTIME_USER_CLIENT, _RUNTIME_USER, _RUNTIME_PROFILE

    access_token = str(st.session_state.get("auth_access_token", ""))
    refresh_token = str(st.session_state.get("auth_refresh_token", ""))

    if not access_token or not refresh_token:
        raise RuntimeError("You are not logged in.")

    try:
        client = create_public_client()
        session_response = client.auth.set_session(access_token, refresh_token)
        refreshed_session = getattr(session_response, "session", None)

        if refreshed_session is not None:
            st.session_state.auth_access_token = str(
                refreshed_session.access_token
            )
            st.session_state.auth_refresh_token = str(
                refreshed_session.refresh_token
            )

        user_response = client.auth.get_user()
        user = getattr(user_response, "user", None)

        if user is None:
            raise RuntimeError("The login session could not be verified.")

        profile_response = (
            client.table("voicebridge_user_profiles")
            .select("*")
            .eq("user_id", str(user.id))
            .limit(1)
            .execute()
        )
        profile_rows = list(profile_response.data or [])

        if not profile_rows:
            raise RuntimeError(
                "The account profile is missing. Contact the platform administrator."
            )

        profile = dict(profile_rows[0])
        st.session_state.auth_user_id = str(user.id)
        st.session_state.auth_email = str(user.email or profile.get("email") or "")

        _RUNTIME_USER_CLIENT = client
        _RUNTIME_USER = user
        _RUNTIME_PROFILE = profile
        return client, user, profile

    except Exception:
        clear_auth_state()
        raise


def get_user_client() -> Client:
    return get_user_context()[0]


def get_current_user() -> Any:
    return get_user_context()[1]


def get_current_profile(silent: bool = False) -> dict[str, Any] | None:
    try:
        return get_user_context()[2]
    except Exception:
        if not silent:
            st.error("Your login session has expired. Please log in again.")
        return None


def is_logged_in() -> bool:
    return bool(
        st.session_state.get("auth_access_token")
        and st.session_state.get("auth_refresh_token")
    )


def is_platform_admin(profile: dict[str, Any] | None = None) -> bool:
    profile = profile or get_current_profile(silent=True)
    return bool(
        profile
        and profile.get("role") == "platform_admin"
        and profile.get("account_status") == "approved"
    )


def has_approved_teacher_access(
    profile: dict[str, Any] | None = None,
) -> bool:
    profile = profile or get_current_profile(silent=True)

    if not profile or profile.get("account_status") != "approved":
        return False

    if profile.get("role") == "platform_admin":
        return True

    return bool(
        profile.get("role") == "teacher_educator"
        and profile.get("workspace_id")
    )


# =======================================================
# GENERAL HELPERS
# =======================================================


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_reference(student_id: str, task_id: str) -> str:
    safe_student_id = re.sub(r"[^A-Za-z0-9]", "", student_id.upper()) or "PST"
    timestamp = datetime.now(IST).strftime("%Y%m%d%H%M%S%f")
    return f"{safe_student_id}-{task_id}-{timestamp}"


def safe_path_segment(value: str, fallback: str = "participant") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "-", value.strip()).strip("-_")
    return cleaned[:80] or fallback


def normalise_workspace_code(value: str) -> str:
    return re.sub(r"[^A-Z0-9-]+", "-", value.upper().strip()).strip("-")[:32]


def audio_extension(mime_type: str) -> str:
    mapping = {
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/webm": ".webm",
        "audio/mpeg": ".mp3",
        "audio/mp4": ".m4a",
    }
    return mapping.get((mime_type or "").lower(), ".wav")


def format_datetime(value: Any) -> str:
    if not value:
        return "Not available"

    try:
        parsed = pd.to_datetime(value, utc=True)
        return parsed.tz_convert("Asia/Kolkata").strftime("%d-%m-%Y %I:%M %p")
    except Exception:
        return str(value)


def is_scored(submission: dict[str, Any]) -> bool:
    return submission.get("total_score") is not None


def clean_error_message(exception: Exception) -> str:
    message = str(exception).strip()
    return (message or "An unexpected connection error occurred.")[:700]


def response_label(submission: dict[str, Any]) -> str:
    return (
        f'{submission.get("student_id", "")} | '
        f'{submission.get("task_id", "")} | '
        f'{submission.get("participant_name", "")} | '
        f'{format_datetime(submission.get("submitted_at"))}'
    )


def require_configuration() -> bool:
    if not CONFIGURATION_ERROR and SERVICE is not None:
        return True

    st.error("The Supabase connection is not configured.")
    st.code(
        "[supabase]\n"
        'url = "https://YOUR-PROJECT.supabase.co"\n'
        'publishable_key = "YOUR-PUBLISHABLE-KEY"\n'
        'secret_key = "YOUR-SECRET-KEY"\n'
        'bucket = "voice-recordings"',
        language="toml",
    )
    if CONFIGURATION_ERROR:
        st.caption(CONFIGURATION_ERROR)
    return False


def require_approved_access() -> bool:
    if not require_configuration():
        return False

    profile = get_current_profile(silent=True)

    if profile is None:
        st.warning("Log in with your Teacher-Educator account to open this page.")
        return False

    if not has_approved_teacher_access(profile):
        st.warning(
            "This page is available only to approved Teacher-Educator accounts."
        )
        return False

    return True


def require_admin_access() -> bool:
    if not require_approved_access():
        return False

    if not is_platform_admin():
        st.error("This page is restricted to the Platform Administrator.")
        return False

    return True


@st.cache_data(ttl=30, show_spinner=False)
def service_connection_status() -> tuple[bool, str]:
    if SERVICE is None:
        return False, CONFIGURATION_ERROR or "Supabase is not configured."

    try:
        SERVICE.table("voicebridge_workspaces").select("id").limit(1).execute()
        SERVICE.table("voicebridge_user_profiles").select("user_id").limit(1).execute()
        SERVICE.table(TABLE_NAME).select("id").limit(1).execute()
        return True, ""
    except Exception as exc:
        return False, clean_error_message(exc)


def find_active_workspace(workspace_code: str) -> dict[str, Any] | None:
    if SERVICE is None:
        raise RuntimeError("Supabase is not configured.")

    code = normalise_workspace_code(workspace_code)
    response = (
        SERVICE.table("voicebridge_workspaces")
        .select("id,workspace_name,workspace_code,institution,is_active")
        .eq("workspace_code", code)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    rows = list(response.data or [])
    return dict(rows[0]) if rows else None


def upload_audio_recording(
    audio_bytes: bytes,
    storage_path: str,
    mime_type: str,
) -> None:
    if SERVICE is None:
        raise RuntimeError("Supabase is not configured.")

    suffix = audio_extension(mime_type)
    temporary_path: str | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            suffix=suffix,
            delete=False,
        ) as temporary_file:
            temporary_file.write(audio_bytes)
            temporary_path = temporary_file.name

        with open(temporary_path, "rb") as binary_file:
            (
                SERVICE.storage.from_(BUCKET_NAME).upload(
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
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)


def fetch_all_submissions() -> list[dict[str, Any]]:
    """Retrieve rows visible to the authenticated user's RLS policy."""

    client = get_user_client()
    rows: list[dict[str, Any]] = []
    page_size = 1000
    start = 0

    while True:
        response = (
            client.table(TABLE_NAME)
            .select("*")
            .order("submitted_at", desc=True)
            .range(start, start + page_size - 1)
            .execute()
        )
        page = list(response.data or [])
        rows.extend(page)

        if len(page) < page_size:
            break

        start += page_size
        if start >= 10000:
            break

    return rows


def select_submission(
    submissions: list[dict[str, Any]],
    label: str,
    key: str,
) -> dict[str, Any] | None:
    if not submissions:
        return None

    references = [row["submission_reference"] for row in submissions]
    labels = {
        row["submission_reference"]: response_label(row)
        for row in submissions
    }

    selected_reference = st.selectbox(
        label,
        references,
        format_func=lambda reference: labels.get(reference, reference),
        key=key,
    )

    return next(
        (
            row
            for row in submissions
            if row["submission_reference"] == selected_reference
        ),
        None,
    )


def download_audio(audio_path: str) -> bytes:
    """Download private audio through the authenticated user's Storage policy."""

    return get_user_client().storage.from_(BUCKET_NAME).download(audio_path)


def generate_feedback(scores: dict[str, int]) -> str:
    strongest_key = max(scores, key=scores.get)
    weakest_key = min(scores, key=scores.get)

    guidance = {
        "conceptual_clarity": (
            "Clarify the central concept and use precise subject terminology."
        ),
        "pedagogical_reasoning": (
            "Explain more clearly why the proposed teaching response is suitable "
            "for the learner and context."
        ),
        "learner_centred_explanation": (
            "Connect the explanation more directly with the learner's prior "
            "knowledge, language, and learning needs."
        ),
        "misconception_diagnosis": (
            "Identify the exact misconception or source of error more precisely."
        ),
        "use_of_example_strategy": (
            "Use a clearer example, activity, analogy, or assessment strategy."
        ),
        "reflective_thinking": (
            "Add deeper reflection on alternatives, limitations, and improvement."
        ),
        "voice_written_alignment": (
            "Improve consistency between the oral reasoning and written response."
        ),
    }

    return (
        f"Strongest area: {RUBRIC_LABELS[strongest_key]}. "
        f"Priority area: {RUBRIC_LABELS[weakest_key]}. "
        f"Suggested action: {guidance[weakest_key]}"
    )


def display_response_content(submission: dict[str, Any]) -> None:
    st.markdown("### Pedagogical Prompt")
    st.info(submission.get("prompt", ""))

    st.markdown("### Voice Reasoning")
    audio_path = submission.get("audio_path")

    if audio_path:
        try:
            with st.spinner("Loading the private audio recording..."):
                audio_bytes = download_audio(audio_path)
            audio_mime_type = submission.get("audio_mime_type") or "audio/wav"
            st.audio(audio_bytes, format=audio_mime_type)
            st.download_button(
                "Download this audio recording",
                data=audio_bytes,
                file_name=(
                    submission.get("audio_file_name")
                    or f'{submission.get("submission_reference", "recording")}.wav'
                ),
                mime=audio_mime_type,
                key=f'audio_download_{submission.get("submission_reference")}',
            )
        except Exception as exc:
            st.error(
                "The audio recording could not be loaded: "
                f"{clean_error_message(exc)}"
            )
    else:
        st.warning("No audio path is stored for this response.")

    st.markdown("### Written Pedagogical Response")
    st.write(submission.get("written_response", ""))

    st.markdown("### Reflection: Identified Issue")
    st.write(submission.get("reflection_issue", ""))

    st.markdown("### Reflection: Proposed Strategy")
    st.write(submission.get("reflection_strategy", ""))


def submissions_to_csv(submissions: list[dict[str, Any]]) -> bytes:
    output = StringIO()
    fields = [
        "submission_reference",
        "workspace_id",
        "student_id",
        "participant_name",
        "semester",
        "pedagogy_subject",
        "task_id",
        "task_category",
        "prompt",
        "written_response",
        "reflection_issue",
        "reflection_strategy",
        "submitted_at",
        "audio_path",
        "audio_file_name",
        "audio_mime_type",
        *RUBRIC_KEYS,
        "total_score",
        "percentage",
        "teacher_feedback",
        "scored_at",
    ]

    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()

    for submission in submissions:
        row = {field: submission.get(field, "") for field in fields}
        if isinstance(row.get("percentage"), (int, float)):
            row["percentage"] = round(float(row["percentage"]), 2)
        writer.writerow(row)

    return output.getvalue().encode("utf-8-sig")

# =======================================================
# HOME PAGE
# =======================================================


def render_home() -> None:
    st.markdown(f"# {MIC_ICON} VoiceBridge-PST Dashboard")
    st.subheader(
        "Voice-First Micro-Pedagogical Reasoning Activity and Analytics Platform"
    )
    st.write("")

    photograph_column, information_column = st.columns([1, 2.8], gap="large")

    with photograph_column:
        if PROFILE_IMAGE.exists():
            st.image(str(PROFILE_IMAGE), width=210)
        else:
            st.warning(
                "Profile photograph not found. Keep MD_pic.png in the same folder "
                "as app.py."
            )

    with information_column:
        st.caption("Conceptualized and Developed by")
        st.markdown("### Dr. Meenakshi Dwivedi")
        st.markdown(
            "Assistant Professor  \n"
            "Department of Education / School of Education  \n"
            "Mahatma Jyotiba Phule Rohilkhand University  \n"
            "Bareilly, Uttar Pradesh, India"
        )

    st.divider()
    st.header("Purpose")
    st.write(
        "VoiceBridge-PST is a voice-first activity and analytics platform designed "
        "to support the assessment and development of micro-pedagogical reasoning "
        "among pre-service teachers."
    )

    st.header("How the Platform Works")
    st.write(
        "Pedagogical Prompt -> Voice Reasoning -> Written Pedagogical Response -> "
        "Reflective Response -> Teacher-Educator Review -> Rubric Scoring -> "
        "Diagnostic Feedback"
    )

    st.header("Permanent and Private Storage")
    st.write(
        "After a participant submits an activity, the voice recording is stored in "
        "the private voice-recordings bucket and the written information is stored "
        "in the VoiceBridge-PST database. Teacher-Educator pages require an individually registered, verified, and approved account. Each approved teacher sees only the submissions assigned to their workspace."
    )

    st.header("Assessment Dimensions")
    for number, (_, label) in enumerate(RUBRIC, start=1):
        st.write(f"{number}. {label}")

# =======================================================
# ACTIVITY SUBMISSION PAGE
# =======================================================


def render_activity_submission() -> None:
    st.title("Activity Submission")

    if not require_configuration():
        return

    connected, connection_error = service_connection_status()
    if not connected:
        st.error("The permanent storage connection is not ready.")
        st.caption(connection_error)
        return

    if "activity_flash" in st.session_state:
        flash = st.session_state.pop("activity_flash")
        st.success(flash["message"])
        st.info(f'Submission reference: {flash["reference"]}')

    st.write(
        "Enter the workspace code given by your Teacher Educator. Then select "
        "your pedagogy subject and task, record your voice reasoning, and complete "
        "the written and reflective responses."
    )

    form_version = st.session_state.activity_form_version

    workspace_code = st.text_input(
        "Teacher Workspace Code",
        placeholder="Example: MJPRU-EDU-01",
        help="This code assigns your response to the correct Teacher Educator.",
        key=f"workspace_code_{form_version}",
    )

    selected_subject = st.selectbox(
        "Pedagogy Subject",
        list(TASK_BANK.keys()),
        key=f"selected_subject_{form_version}",
    )

    tasks = TASK_BANK[selected_subject]
    task_labels = [f"{task_id} - {category}" for task_id, category, _ in tasks]

    selected_task_label = st.selectbox(
        "Task",
        task_labels,
        key=f"task_select_{selected_subject}_{form_version}",
    )

    selected_task_index = task_labels.index(selected_task_label)
    task_id, task_category, prompt = tasks[selected_task_index]

    st.markdown("### Pedagogical Prompt")
    st.info(prompt)

    task_column_1, task_column_2 = st.columns(2)
    task_column_1.text_input("Task ID", value=task_id, disabled=True)
    task_column_2.text_input("Task Category", value=task_category, disabled=True)

    st.divider()
    st.markdown("## Stage 1: Voice Reasoning")
    st.write(
        "Think aloud and explain how you understand the pedagogical situation and "
        "how you would respond as a teacher."
    )
    st.caption(
        "Suggested duration: 2-3 minutes. Allow microphone access when requested. "
        "Maximum accepted recording size: 10 MB."
    )

    audio_response = st.audio_input(
        "Record your voice response",
        key=f"audio_{task_id}_{form_version}",
    )

    if audio_response is not None:
        audio_size = len(audio_response.getvalue())
        st.audio(audio_response)
        if audio_size <= MAX_AUDIO_BYTES:
            st.success(f"Voice response recorded ({audio_size / 1024:.1f} KB).")
        else:
            st.error("The recording is larger than 10 MB. Record a shorter response.")

    st.divider()

    with st.form(f"activity_form_{form_version}", border=True):
        st.markdown("## Participant Details")
        participant_column_1, participant_column_2 = st.columns(2)

        with participant_column_1:
            student_id = st.text_input(
                "Student ID / Participant Code",
                placeholder="Example: PST001",
                key=f"student_id_{form_version}",
            )
            participant_name = st.text_input(
                "Name",
                placeholder="Enter your name",
                key=f"participant_name_{form_version}",
            )

        with participant_column_2:
            semester = st.selectbox(
                "B.Ed. Semester",
                ["Semester I", "Semester II", "Semester III", "Semester IV"],
                key=f"semester_{form_version}",
            )
            st.text_input(
                "Selected Pedagogy Subject",
                value=selected_subject,
                disabled=True,
                key=f"subject_display_{form_version}",
            )

        st.markdown("## Stage 2: Written Pedagogical Response")
        written_response = st.text_area(
            "Explain how you would respond to the pedagogical situation.",
            placeholder=(
                "Describe what you would say or do as a teacher and explain the "
                "reasoning behind your response."
            ),
            height=180,
            key=f"written_response_{form_version}",
        )
        st.caption("Suggested length: approximately 150-200 words.")

        st.markdown("## Stage 3: Reflective Response")
        reflection_issue = st.text_area(
            "What learner difficulty, misconception, error, or pedagogical issue "
            "did you identify?",
            height=120,
            key=f"reflection_issue_{form_version}",
        )
        reflection_strategy = st.text_area(
            "What example, activity, explanation, assessment method, or teaching "
            "strategy would you use?",
            height=120,
            key=f"reflection_strategy_{form_version}",
        )

        declaration = st.checkbox(
            "I confirm that the voice and written responses are my own work.",
            key=f"declaration_{form_version}",
        )

        submit_response = st.form_submit_button(
            "Submit Activity",
            type="primary",
        )

    if not submit_response:
        return

    errors: list[str] = []
    audio_bytes = audio_response.getvalue() if audio_response is not None else b""

    if not workspace_code.strip():
        errors.append("Enter the Teacher Workspace Code.")
    if not student_id.strip():
        errors.append("Enter your Student ID / Participant Code.")
    if not participant_name.strip():
        errors.append("Enter your name.")
    if audio_response is None:
        errors.append("Record your voice response.")
    elif len(audio_bytes) > MAX_AUDIO_BYTES:
        errors.append("The recording must be 10 MB or smaller.")
    if not written_response.strip():
        errors.append("Enter your written pedagogical response.")
    if not reflection_issue.strip():
        errors.append("Complete the identified-issue reflection.")
    if not reflection_strategy.strip():
        errors.append("Complete the proposed-strategy reflection.")
    if not declaration:
        errors.append("Confirm the originality declaration.")

    if errors:
        st.error("Please complete the following before submitting:")
        for error in errors:
            st.write(f"- {error}")
        return

    try:
        workspace = find_active_workspace(workspace_code)
    except Exception as exc:
        st.error(f"The workspace code could not be checked: {clean_error_message(exc)}")
        return

    if workspace is None:
        st.error(
            "The workspace code is invalid or inactive. Check the code with your "
            "Teacher Educator."
        )
        return

    submission_reference = make_reference(student_id.strip(), task_id)
    audio_mime_type = getattr(audio_response, "type", None) or "audio/wav"
    extension = audio_extension(audio_mime_type)
    participant_folder = safe_path_segment(student_id, "participant")
    date_folder = datetime.now(IST).strftime("%Y/%m/%d")
    workspace_id = str(workspace["id"])
    audio_path = (
        f"{workspace_id}/{date_folder}/{participant_folder}/"
        f"{safe_path_segment(submission_reference, 'recording')}{extension}"
    )
    audio_file_name = f"{submission_reference}{extension}"

    database_record = {
        "submission_reference": submission_reference,
        "workspace_id": workspace_id,
        "student_id": student_id.strip(),
        "participant_name": participant_name.strip(),
        "semester": semester,
        "pedagogy_subject": selected_subject,
        "task_id": task_id,
        "task_category": task_category,
        "prompt": prompt,
        "audio_path": audio_path,
        "audio_file_name": audio_file_name,
        "audio_mime_type": audio_mime_type,
        "written_response": written_response.strip(),
        "reflection_issue": reflection_issue.strip(),
        "reflection_strategy": reflection_strategy.strip(),
    }

    uploaded = False

    try:
        with st.spinner("Uploading the voice recording and saving the response..."):
            upload_audio_recording(
                audio_bytes=audio_bytes,
                storage_path=audio_path,
                mime_type=audio_mime_type,
            )
            uploaded = True
            SERVICE.table(TABLE_NAME).insert(database_record).execute()

        st.session_state.activity_flash = {
            "message": (
                "Your activity has been submitted successfully to "
                f'{workspace.get("workspace_name", "the selected workspace")}.'
            ),
            "reference": submission_reference,
        }
        st.session_state.activity_form_version += 1
        st.rerun()

    except Exception as exc:
        if uploaded:
            try:
                SERVICE.storage.from_(BUCKET_NAME).remove([audio_path])
            except Exception:
                pass

        st.error(
            "The submission could not be saved. Your form has not been cleared. "
            "Please try again."
        )
        st.caption(clean_error_message(exc))


# =======================================================
# ACCOUNT CREATION AND LOGIN
# =======================================================


def render_create_account() -> None:
    st.title("Create Teacher-Educator Account")

    if not require_configuration():
        return

    st.info(
        "Create your own account. After email verification, the Platform "
        "Administrator must approve the account and assign a workspace before "
        "Teacher-Educator pages become available."
    )

    with st.form("teacher_registration_form", border=True):
        full_name = st.text_input("Full Name")
        institution = st.text_input("Institution / University")
        department = st.text_input("Department / School")
        email = st.text_input("Official Email Address")
        password = st.text_input("Create Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        declaration = st.checkbox(
            "I confirm that I am requesting access as a Teacher Educator."
        )
        register_clicked = st.form_submit_button(
            "Create Account",
            type="primary",
        )

    if not register_clicked:
        return

    errors: list[str] = []
    if not full_name.strip():
        errors.append("Enter your full name.")
    if not institution.strip():
        errors.append("Enter your institution.")
    if not email.strip() or "@" not in email:
        errors.append("Enter a valid email address.")
    if len(password) < 8:
        errors.append("Use a password containing at least 8 characters.")
    if password != confirm_password:
        errors.append("The two password entries do not match.")
    if not declaration:
        errors.append("Confirm the Teacher-Educator account declaration.")

    if errors:
        st.error("Please correct the following:")
        for error in errors:
            st.write(f"- {error}")
        return

    try:
        client = create_public_client()
        response = client.auth.sign_up(
            {
                "email": email.strip().lower(),
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name.strip(),
                        "institution": institution.strip(),
                        "department": department.strip(),
                    }
                },
            }
        )

        if getattr(response, "session", None) is not None:
            store_auth_session(response)
            st.success(
                "Account created. Your request is pending administrator approval."
            )
            st.rerun()
        else:
            st.success(
                "Account created. Open the verification email sent by Supabase, "
                "confirm your email address, and then return here to log in. Your "
                "account will remain pending until the Platform Administrator "
                "approves it."
            )

    except Exception as exc:
        st.error(f"The account could not be created: {clean_error_message(exc)}")


def render_teacher_login() -> None:
    st.title("Teacher-Educator Login")

    if not require_configuration():
        return

    if is_logged_in():
        profile = get_current_profile(silent=True)
        if profile:
            st.success(
                f'Logged in as {profile.get("full_name", st.session_state.auth_email)}.'
            )
            st.write("Use the pages now shown in the sidebar.")
            return

    with st.form("teacher_login_form", border=True):
        email = st.text_input("Email Address")
        password = st.text_input("Password", type="password")
        login_clicked = st.form_submit_button("Log in", type="primary")

    if not login_clicked:
        st.caption(
            "New users must first create an account and verify their email address."
        )
        return

    try:
        client = create_public_client()
        response = client.auth.sign_in_with_password(
            {
                "email": email.strip().lower(),
                "password": password,
            }
        )
        store_auth_session(response)
        get_user_context()
        st.success("Login successful.")
        st.rerun()
    except Exception as exc:
        clear_auth_state()
        st.error(
            "Login failed. Check the email, password, and email verification status."
        )
        st.caption(clean_error_message(exc))


def render_account_status() -> None:
    st.title("Account Status")

    profile = get_current_profile()
    if profile is None:
        return

    status = str(profile.get("account_status", "pending"))
    role = str(profile.get("role", "teacher_educator"))

    st.write(f'**Name:** {profile.get("full_name", "")}')
    st.write(f'**Email:** {profile.get("email", "")}')
    st.write(f'**Institution:** {profile.get("institution", "")}')
    st.write(f'**Department:** {profile.get("department", "") or "Not provided"}')
    st.write(f'**Role:** {role.replace("_", " ").title()}')

    if status == "pending":
        st.warning(
            "Your email account is active, but Teacher-Educator access is pending "
            "administrator approval."
        )
    elif status == "rejected":
        st.error("The account request was not approved.")
        if profile.get("rejection_reason"):
            st.write(f'**Reason:** {profile.get("rejection_reason")}')
    elif status == "suspended":
        st.error("This account is temporarily suspended.")
    elif status == "approved":
        st.success("Your account is approved.")

        if role == "teacher_educator" and profile.get("workspace_id"):
            try:
                workspace_response = (
                    get_user_client()
                    .table("voicebridge_workspaces")
                    .select("workspace_name,workspace_code,institution,is_active")
                    .eq("id", profile["workspace_id"])
                    .limit(1)
                    .execute()
                )
                workspaces = list(workspace_response.data or [])
                if workspaces:
                    workspace = workspaces[0]
                    st.info(
                        f'Workspace: {workspace.get("workspace_name")}  |  '
                        f'Code: {workspace.get("workspace_code")}'
                    )
            except Exception as exc:
                st.caption(clean_error_message(exc))


def render_my_account() -> None:
    st.title("My Account")

    profile = get_current_profile()
    if profile is None:
        return

    st.subheader("Profile")

    with st.form("profile_update_form", border=True):
        full_name = st.text_input(
            "Full Name",
            value=str(profile.get("full_name") or ""),
        )
        institution = st.text_input(
            "Institution / University",
            value=str(profile.get("institution") or ""),
        )
        department = st.text_input(
            "Department / School",
            value=str(profile.get("department") or ""),
        )
        profile_update_clicked = st.form_submit_button("Update Profile")

    if profile_update_clicked:
        try:
            (
                get_user_client()
                .table("voicebridge_user_profiles")
                .update(
                    {
                        "full_name": full_name.strip(),
                        "institution": institution.strip(),
                        "department": department.strip(),
                    }
                )
                .eq("user_id", profile["user_id"])
                .execute()
            )
            global _RUNTIME_PROFILE
            _RUNTIME_PROFILE = None
            st.success("Profile updated.")
            st.rerun()
        except Exception as exc:
            st.error(f"Profile could not be updated: {clean_error_message(exc)}")

    st.subheader("Change Password")

    with st.form("change_password_form", border=True):
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        password_clicked = st.form_submit_button("Change Password")

    if password_clicked:
        if len(new_password) < 8:
            st.error("Use a password containing at least 8 characters.")
        elif new_password != confirm_password:
            st.error("The two password entries do not match.")
        else:
            try:
                get_user_client().auth.update_user({"password": new_password})
                st.success("Password changed successfully.")
            except Exception as exc:
                st.error(f"Password could not be changed: {clean_error_message(exc)}")


# =======================================================
# PLATFORM ADMINISTRATOR: USER MANAGEMENT
# =======================================================


def fetch_admin_profiles() -> list[dict[str, Any]]:
    if SERVICE is None:
        raise RuntimeError("Supabase is not configured.")
    response = (
        SERVICE.table("voicebridge_user_profiles")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return list(response.data or [])


def fetch_admin_workspaces() -> list[dict[str, Any]]:
    if SERVICE is None:
        raise RuntimeError("Supabase is not configured.")
    response = (
        SERVICE.table("voicebridge_workspaces")
        .select("*")
        .order("workspace_name")
        .execute()
    )
    return list(response.data or [])


def render_admin_user_management() -> None:
    st.title("Admin User Management")

    if not require_admin_access():
        return

    current_admin = get_current_user()

    try:
        profiles = fetch_admin_profiles()
        workspaces = fetch_admin_workspaces()
    except Exception as exc:
        st.error(f"User information could not be loaded: {clean_error_message(exc)}")
        return

    pending_profiles = [
        profile
        for profile in profiles
        if profile.get("account_status") == "pending"
        and profile.get("role") == "teacher_educator"
    ]

    metric_1, metric_2, metric_3, metric_4 = st.columns(4)
    metric_1.metric("Pending Requests", len(pending_profiles))
    metric_2.metric(
        "Approved Teachers",
        len(
            [
                p
                for p in profiles
                if p.get("role") == "teacher_educator"
                and p.get("account_status") == "approved"
            ]
        ),
    )
    metric_3.metric("Workspaces", len(workspaces))
    metric_4.metric("All Accounts", len(profiles))

    approval_tab, accounts_tab, workspaces_tab = st.tabs(
        ["Pending Approval", "All Accounts", "Workspaces"]
    )

    with approval_tab:
        if not pending_profiles:
            st.success("There are no pending Teacher-Educator requests.")
        else:
            profile_lookup = {
                str(profile["user_id"]): profile
                for profile in pending_profiles
            }
            selected_user_id = st.selectbox(
                "Select a pending request",
                list(profile_lookup.keys()),
                format_func=lambda user_id: (
                    f'{profile_lookup[user_id].get("full_name")} | '
                    f'{profile_lookup[user_id].get("email")} | '
                    f'{profile_lookup[user_id].get("institution")}'
                ),
                key="pending_user_selector",
            )
            selected_profile = profile_lookup[selected_user_id]

            st.write(f'**Name:** {selected_profile.get("full_name")}')
            st.write(f'**Email:** {selected_profile.get("email")}')
            st.write(f'**Institution:** {selected_profile.get("institution")}')
            st.write(
                f'**Department:** {selected_profile.get("department") or "Not provided"}'
            )
            st.write(
                f'**Requested:** {format_datetime(selected_profile.get("created_at"))}'
            )

            assignment_mode = st.radio(
                "Workspace assignment",
                ["Create a new workspace", "Assign an existing workspace"],
                horizontal=True,
                key="workspace_assignment_mode",
            )

            selected_workspace_id: str | None = None
            new_workspace_name = ""
            new_workspace_code = ""
            new_workspace_institution = str(
                selected_profile.get("institution") or ""
            )

            if assignment_mode == "Create a new workspace":
                default_code = normalise_workspace_code(
                    f'{selected_profile.get("institution", "EDU")[:12]}-'
                    f'{selected_profile.get("full_name", "TEACHER")[:8]}'
                )
                new_workspace_name = st.text_input(
                    "Workspace Name",
                    value=(
                        f'{selected_profile.get("institution", "Institution")} - '
                        f'{selected_profile.get("full_name", "Teacher")}'
                    ),
                )
                new_workspace_code = st.text_input(
                    "Workspace Code",
                    value=default_code,
                    help="Use 4-32 uppercase letters, numbers, or hyphens.",
                )
                new_workspace_institution = st.text_input(
                    "Workspace Institution",
                    value=new_workspace_institution,
                )
            else:
                active_workspaces = [w for w in workspaces if w.get("is_active")]
                if active_workspaces:
                    workspace_lookup = {
                        str(workspace["id"]): workspace
                        for workspace in active_workspaces
                    }
                    selected_workspace_id = st.selectbox(
                        "Existing Workspace",
                        list(workspace_lookup.keys()),
                        format_func=lambda workspace_id: (
                            f'{workspace_lookup[workspace_id].get("workspace_name")} | '
                            f'{workspace_lookup[workspace_id].get("workspace_code")}'
                        ),
                    )
                else:
                    st.warning("No active workspace exists. Create a new workspace.")

            approve_column, reject_column = st.columns(2)

            with approve_column:
                approve_clicked = st.button(
                    "Approve Teacher Account",
                    type="primary",
                    use_container_width=True,
                )

            with reject_column:
                rejection_reason = st.text_input(
                    "Rejection reason",
                    key="rejection_reason",
                )
                reject_clicked = st.button(
                    "Reject Request",
                    use_container_width=True,
                )

            if approve_clicked:
                try:
                    if assignment_mode == "Create a new workspace":
                        code = normalise_workspace_code(new_workspace_code)
                        if len(code) < 4:
                            raise ValueError(
                                "Workspace code must contain at least 4 valid characters."
                            )
                        if not new_workspace_name.strip():
                            raise ValueError("Enter a workspace name.")

                        workspace_response = (
                            SERVICE.table("voicebridge_workspaces")
                            .insert(
                                {
                                    "workspace_name": new_workspace_name.strip(),
                                    "workspace_code": code,
                                    "institution": new_workspace_institution.strip(),
                                    "owner_user_id": selected_user_id,
                                    "is_active": True,
                                }
                            )
                            .execute()
                        )
                        created = list(workspace_response.data or [])
                        if not created:
                            raise RuntimeError("The workspace was not created.")
                        selected_workspace_id = str(created[0]["id"])
                    elif not selected_workspace_id:
                        raise ValueError("Select an existing workspace.")

                    (
                        SERVICE.table("voicebridge_user_profiles")
                        .update(
                            {
                                "role": "teacher_educator",
                                "account_status": "approved",
                                "workspace_id": selected_workspace_id,
                                "approved_at": now_utc_iso(),
                                "approved_by": str(current_admin.id),
                                "rejection_reason": None,
                            }
                        )
                        .eq("user_id", selected_user_id)
                        .execute()
                    )
                    st.success("The Teacher-Educator account has been approved.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Approval failed: {clean_error_message(exc)}")

            if reject_clicked:
                try:
                    (
                        SERVICE.table("voicebridge_user_profiles")
                        .update(
                            {
                                "account_status": "rejected",
                                "workspace_id": None,
                                "approved_at": None,
                                "approved_by": str(current_admin.id),
                                "rejection_reason": (
                                    rejection_reason.strip()
                                    or "The account request was not approved."
                                ),
                            }
                        )
                        .eq("user_id", selected_user_id)
                        .execute()
                    )
                    st.success("The account request has been rejected.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Rejection failed: {clean_error_message(exc)}")

    with accounts_tab:
        account_rows = []
        workspace_names = {
            str(workspace["id"]): workspace.get("workspace_name")
            for workspace in workspaces
        }
        for profile in profiles:
            account_rows.append(
                {
                    "Name": profile.get("full_name"),
                    "Email": profile.get("email"),
                    "Institution": profile.get("institution"),
                    "Role": str(profile.get("role", "")).replace("_", " ").title(),
                    "Status": str(profile.get("account_status", "")).title(),
                    "Workspace": workspace_names.get(
                        str(profile.get("workspace_id")), ""
                    ),
                    "Created": format_datetime(profile.get("created_at")),
                }
            )
        st.dataframe(
            pd.DataFrame(account_rows),
            hide_index=True,
            use_container_width=True,
        )

        manageable = [
            profile
            for profile in profiles
            if str(profile.get("user_id")) != str(current_admin.id)
        ]
        if manageable:
            manage_lookup = {
                str(profile["user_id"]): profile
                for profile in manageable
            }
            manage_user_id = st.selectbox(
                "Manage an existing account",
                list(manage_lookup.keys()),
                format_func=lambda user_id: (
                    f'{manage_lookup[user_id].get("full_name")} | '
                    f'{manage_lookup[user_id].get("account_status")}'
                ),
                key="manage_existing_account",
            )
            manage_profile = manage_lookup[manage_user_id]
            action = st.selectbox(
                "Account action",
                ["No action", "Suspend account", "Reactivate as pending"],
            )
            if st.button("Apply Account Action"):
                try:
                    if action == "Suspend account":
                        new_status = "suspended"
                    elif action == "Reactivate as pending":
                        new_status = "pending"
                    else:
                        st.info("Select an action first.")
                        return

                    update_values: dict[str, Any] = {
                        "account_status": new_status,
                    }
                    if new_status == "pending":
                        update_values.update(
                            {
                                "workspace_id": None,
                                "approved_at": None,
                                "rejection_reason": None,
                            }
                        )

                    (
                        SERVICE.table("voicebridge_user_profiles")
                        .update(update_values)
                        .eq("user_id", manage_user_id)
                        .execute()
                    )
                    st.success("Account status updated.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Account update failed: {clean_error_message(exc)}")

    with workspaces_tab:
        st.subheader("Create Workspace")
        with st.form("admin_create_workspace_form", border=True):
            create_name = st.text_input("Workspace Name")
            create_code = st.text_input(
                "Workspace Code",
                placeholder="Example: MJPRU-EDU-01",
            )
            create_institution = st.text_input("Institution")
            create_workspace_clicked = st.form_submit_button(
                "Create Workspace",
                type="primary",
            )

        if create_workspace_clicked:
            try:
                code = normalise_workspace_code(create_code)
                if len(code) < 4:
                    raise ValueError(
                        "Workspace code must contain at least 4 valid characters."
                    )
                if not create_name.strip():
                    raise ValueError("Enter a workspace name.")

                (
                    SERVICE.table("voicebridge_workspaces")
                    .insert(
                        {
                            "workspace_name": create_name.strip(),
                            "workspace_code": code,
                            "institution": create_institution.strip(),
                            "owner_user_id": str(current_admin.id),
                            "is_active": True,
                        }
                    )
                    .execute()
                )
                st.success("Workspace created successfully.")
                st.rerun()
            except Exception as exc:
                st.error(f"Workspace creation failed: {clean_error_message(exc)}")

        st.subheader("Existing Workspaces")
        workspace_rows = [
            {
                "Workspace": workspace.get("workspace_name"),
                "Code": workspace.get("workspace_code"),
                "Institution": workspace.get("institution"),
                "Active": "Yes" if workspace.get("is_active") else "No",
                "Created": format_datetime(workspace.get("created_at")),
            }
            for workspace in workspaces
        ]
        st.dataframe(
            pd.DataFrame(workspace_rows),
            hide_index=True,
            use_container_width=True,
        )

# =======================================================
# REVIEW RESPONSES PAGE
# =======================================================


def render_review_responses() -> None:
    st.title("Review Responses")

    if not require_approved_access():
        return

    try:
        submissions = fetch_all_submissions()
    except Exception as exc:
        st.error(f"Responses could not be retrieved: {clean_error_message(exc)}")
        return

    if not submissions:
        st.warning("No responses have been submitted yet.")
        return

    filter_column_1, filter_column_2 = st.columns(2)

    with filter_column_1:
        subject_options = ["All subjects"] + sorted(
            {row.get("pedagogy_subject", "") for row in submissions if row.get("pedagogy_subject")}
        )
        selected_subject = st.selectbox(
            "Filter by subject",
            subject_options,
            key="review_subject_filter",
        )

    with filter_column_2:
        score_status = st.selectbox(
            "Filter by scoring status",
            ["All responses", "Not scored", "Scored"],
            key="review_score_filter",
        )

    filtered = submissions
    if selected_subject != "All subjects":
        filtered = [
            row for row in filtered if row.get("pedagogy_subject") == selected_subject
        ]
    if score_status == "Not scored":
        filtered = [row for row in filtered if not is_scored(row)]
    elif score_status == "Scored":
        filtered = [row for row in filtered if is_scored(row)]

    st.caption(f"Responses matching the filter: {len(filtered)}")

    selected_submission = select_submission(
        filtered,
        "Select a response",
        "review_response_selector",
    )

    if selected_submission is None:
        st.warning("No response matches the selected filters.")
        return

    st.divider()
    detail_column_1, detail_column_2, detail_column_3 = st.columns(3)
    detail_column_1.metric("Participant Code", selected_submission.get("student_id", ""))
    detail_column_2.metric("Task", selected_submission.get("task_id", ""))
    detail_column_3.metric("Semester", selected_submission.get("semester", ""))

    st.markdown("### Participant Information")
    st.write(f'**Name:** {selected_submission.get("participant_name", "")}')
    st.write(f'**Pedagogy Subject:** {selected_submission.get("pedagogy_subject", "")}')
    st.write(f'**Task Category:** {selected_submission.get("task_category", "")}')
    st.write(f'**Submission Time:** {format_datetime(selected_submission.get("submitted_at"))}')
    st.write(f'**Reference:** {selected_submission.get("submission_reference", "")}')

    display_response_content(selected_submission)

    if is_scored(selected_submission):
        st.markdown("### Saved Rubric Scores")
        score_dataframe = pd.DataFrame(
            {
                "Dimension": [label for _, label in RUBRIC],
                "Score": [selected_submission.get(key) for key, _ in RUBRIC],
            }
        )
        st.dataframe(score_dataframe, hide_index=True, use_container_width=True)

        score_column_1, score_column_2 = st.columns(2)
        score_column_1.metric(
            "Total Score",
            f'{selected_submission.get("total_score", 0)}/{MAX_SCORE}',
        )
        score_column_2.metric(
            "Percentage",
            f'{float(selected_submission.get("percentage") or 0):.2f}%',
        )
        st.markdown("### Teacher-Educator Feedback")
        st.info(selected_submission.get("teacher_feedback") or "No feedback entered.")
        st.caption(f'Scored at: {format_datetime(selected_submission.get("scored_at"))}')


# =======================================================
# SCORE RESPONSES PAGE
# =======================================================


def render_score_responses() -> None:
    st.title("Score Responses")

    if not require_approved_access():
        return

    if "score_flash" in st.session_state:
        st.success(st.session_state.pop("score_flash"))

    try:
        submissions = fetch_all_submissions()
    except Exception as exc:
        st.error(f"Responses could not be retrieved: {clean_error_message(exc)}")
        return

    if not submissions:
        st.warning("No responses are available for scoring.")
        return

    scoring_filter = st.radio(
        "Show",
        ["Unscored responses", "All responses"],
        horizontal=True,
        key="scoring_filter",
    )

    available = (
        [row for row in submissions if not is_scored(row)]
        if scoring_filter == "Unscored responses"
        else submissions
    )

    if not available:
        st.success("All submitted responses have been scored.")
        return

    selected_submission = select_submission(
        available,
        "Select a response to score",
        "score_response_selector",
    )

    if selected_submission is None:
        return

    with st.expander("Review participant response before scoring", expanded=True):
        display_response_content(selected_submission)

    st.markdown("### Rubric Scoring")
    st.caption(
        "1 = Very weak, 2 = Weak, 3 = Satisfactory, 4 = Good, 5 = Excellent."
    )

    score_version = st.session_state.score_form_version
    reference = selected_submission["submission_reference"]

    with st.form(f"score_form_{reference}_{score_version}", border=True):
        entered_scores: dict[str, int] = {}
        left_column, right_column = st.columns(2)

        for index, (rubric_key, rubric_label) in enumerate(RUBRIC):
            target_column = left_column if index % 2 == 0 else right_column
            existing_value = selected_submission.get(rubric_key)
            default_value = int(existing_value) if existing_value is not None else 3

            with target_column:
                entered_scores[rubric_key] = st.slider(
                    rubric_label,
                    min_value=1,
                    max_value=5,
                    value=default_value,
                    step=1,
                    key=(
                        f"score_{reference}_{rubric_key}_{score_version}"
                    ),
                )

        calculated_total = sum(entered_scores.values())
        calculated_percentage = calculated_total / MAX_SCORE * 100

        metric_column_1, metric_column_2 = st.columns(2)
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
            value=selected_submission.get("teacher_feedback") or "",
            height=140,
            placeholder=(
                "Leave blank to use automatically generated diagnostic feedback."
            ),
            key=f"teacher_feedback_{reference}_{score_version}",
        )

        save_scores = st.form_submit_button(
            "Save Scores and Feedback",
            type="primary",
        )

    if not save_scores:
        return

    update_record: dict[str, Any] = {
        **entered_scores,
        "total_score": calculated_total,
        "percentage": round(calculated_percentage, 2),
        "teacher_feedback": (
            teacher_feedback.strip() or generate_feedback(entered_scores)
        ),
        "scored_at": now_utc_iso(),
    }

    try:
        with st.spinner("Saving scores and feedback..."):
            (
                get_user_client().table(TABLE_NAME)
                .update(update_record)
                .eq("submission_reference", reference)
                .execute()
            )

        st.session_state.score_flash = (
            f'Scores saved for {selected_submission.get("student_id", "")} - '
            f'{selected_submission.get("task_id", "")}.'
        )
        st.session_state.score_form_version += 1
        st.rerun()
    except Exception as exc:
        st.error(f"Scores could not be saved: {clean_error_message(exc)}")


# =======================================================
# DIAGNOSTIC PROFILE PAGE
# =======================================================


def render_diagnostic_profile() -> None:
    st.title("Diagnostic Profile")

    if not require_approved_access():
        return

    try:
        submissions = fetch_all_submissions()
    except Exception as exc:
        st.error(f"Scored data could not be retrieved: {clean_error_message(exc)}")
        return

    scored_submissions = [row for row in submissions if is_scored(row)]

    if not scored_submissions:
        st.warning("No scored responses are available.")
        return

    participant_ids = sorted(
        {row.get("student_id", "") for row in scored_submissions if row.get("student_id")}
    )
    selected_student_id = st.selectbox(
        "Select Participant Code",
        participant_ids,
        key="diagnostic_participant",
    )

    participant_submissions = [
        row for row in scored_submissions if row.get("student_id") == selected_student_id
    ]
    participant_submissions.sort(key=lambda row: row.get("submitted_at") or "")
    latest = participant_submissions[-1]

    st.subheader(f"Diagnostic Profile: {selected_student_id}")

    profile_column_1, profile_column_2, profile_column_3 = st.columns(3)
    profile_column_1.metric("Name", latest.get("participant_name", ""))
    profile_column_2.metric("Semester", latest.get("semester", ""))
    profile_column_3.metric("Scored Tasks", len(participant_submissions))

    dimension_means: dict[str, float] = {}
    for rubric_key, _ in RUBRIC:
        values = [
            float(row[rubric_key])
            for row in participant_submissions
            if row.get(rubric_key) is not None
        ]
        dimension_means[rubric_key] = sum(values) / len(values) if values else 0.0

    percentages = [
        float(row.get("percentage") or 0) for row in participant_submissions
    ]
    average_percentage = sum(percentages) / len(percentages)
    strongest_key = max(dimension_means, key=dimension_means.get)
    weakest_key = min(dimension_means, key=dimension_means.get)

    summary_column_1, summary_column_2, summary_column_3 = st.columns(
        [1, 1.4, 1.4]
    )
    summary_column_1.metric("Average Percentage", f"{average_percentage:.2f}%")

    with summary_column_2:
        st.caption("Strongest Area")
        st.success(RUBRIC_LABELS[strongest_key])

    with summary_column_3:
        st.caption("Priority Area")
        st.warning(RUBRIC_LABELS[weakest_key])

    st.markdown("### Dimension-Wise Profile")
    profile_dataframe = pd.DataFrame(
        {
            "Dimension": [label for _, label in RUBRIC],
            "Average Score": [
                round(dimension_means[key], 2) for key, _ in RUBRIC
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

    st.markdown("### Task-Wise Performance")
    task_dataframe = pd.DataFrame(
        [
            {
                "Task": row.get("task_id"),
                "Subject": row.get("pedagogy_subject"),
                "Category": row.get("task_category"),
                "Total Score": row.get("total_score"),
                "Percentage": round(float(row.get("percentage") or 0), 2),
                "Scored Time": format_datetime(row.get("scored_at")),
            }
            for row in participant_submissions
        ]
    )
    st.dataframe(
        task_dataframe,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Subject": st.column_config.TextColumn("Pedagogy Subject", width="large"),
            "Category": st.column_config.TextColumn("Task Category", width="large"),
            "Percentage": st.column_config.NumberColumn(
                "Percentage (%)", format="%.2f"
            ),
        },
    )

    st.markdown("### Latest Diagnostic Feedback")
    st.info(latest.get("teacher_feedback") or "No feedback entered.")


# =======================================================
# TASK ANALYTICS PAGE
# =======================================================


def render_task_analytics() -> None:
    st.title("Task Analytics")

    if not require_approved_access():
        return

    try:
        submissions = fetch_all_submissions()
    except Exception as exc:
        st.error(f"Analytics data could not be retrieved: {clean_error_message(exc)}")
        return

    scored_submissions = [row for row in submissions if is_scored(row)]

    analytics_column_1, analytics_column_2, analytics_column_3, analytics_column_4 = st.columns(4)
    analytics_column_1.metric(
        "Participants",
        len({row.get("student_id") for row in submissions if row.get("student_id")}),
    )
    analytics_column_2.metric("Submissions", len(submissions))
    analytics_column_3.metric("Scored Responses", len(scored_submissions))

    mean_percentage = (
        sum(float(row.get("percentage") or 0) for row in scored_submissions)
        / len(scored_submissions)
        if scored_submissions
        else 0.0
    )
    analytics_column_4.metric("Mean Percentage", f"{mean_percentage:.2f}%")

    if not scored_submissions:
        st.warning("No scored data are available for analytics.")
        return

    subject_options = ["All subjects"] + sorted(
        {row.get("pedagogy_subject", "") for row in scored_submissions if row.get("pedagogy_subject")}
    )
    selected_subject = st.selectbox(
        "Analyse",
        subject_options,
        key="analytics_subject_filter",
    )

    analysed_rows = scored_submissions
    if selected_subject != "All subjects":
        analysed_rows = [
            row for row in scored_submissions if row.get("pedagogy_subject") == selected_subject
        ]

    analytics_dataframe = pd.DataFrame(
        [
            {
                "Participant": row.get("student_id"),
                "Name": row.get("participant_name"),
                "Subject": row.get("pedagogy_subject"),
                "Task": row.get("task_id"),
                "Category": row.get("task_category"),
                "Total Score": row.get("total_score"),
                "Percentage": round(float(row.get("percentage") or 0), 2),
                **{
                    rubric_label: row.get(rubric_key)
                    for rubric_key, rubric_label in RUBRIC
                },
            }
            for row in analysed_rows
        ]
    )

    st.markdown("### Subject-Wise Mean Percentage")
    subject_summary = (
        analytics_dataframe.groupby("Subject", as_index=False)["Percentage"]
        .mean()
        .sort_values("Percentage", ascending=False)
    )
    subject_summary["Percentage"] = subject_summary["Percentage"].round(2)

    if len(subject_summary) == 1:
        st.metric(
            str(subject_summary.iloc[0]["Subject"]),
            f'{float(subject_summary.iloc[0]["Percentage"]):.2f}%',
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
            "Subject": st.column_config.TextColumn("Pedagogy Subject", width="large"),
            "Percentage": st.column_config.NumberColumn(
                "Mean Percentage (%)", format="%.2f"
            ),
        },
    )

    st.markdown("### Task-Wise Mean Percentage")
    task_summary = (
        analytics_dataframe.groupby("Task", as_index=False)["Percentage"]
        .mean()
        .sort_values("Task")
    )
    task_summary["Percentage"] = task_summary["Percentage"].round(2)
    st.bar_chart(task_summary, x="Task", y="Percentage", height=300)
    st.dataframe(
        task_summary,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Percentage": st.column_config.NumberColumn(
                "Mean Percentage (%)", format="%.2f"
            )
        },
    )

    st.markdown("### Category-Wise Mean Percentage")
    category_summary = (
        analytics_dataframe.groupby("Category", as_index=False)["Percentage"]
        .mean()
        .sort_values("Percentage", ascending=False)
    )
    category_summary["Percentage"] = category_summary["Percentage"].round(2)
    st.bar_chart(
        category_summary,
        x="Percentage",
        y="Category",
        horizontal=True,
        height=300,
    )

    st.markdown("### Dimension-Wise Mean Scores")
    dimension_summary = pd.DataFrame(
        {
            "Dimension": [label for _, label in RUBRIC],
            "Mean Score": [
                round(float(analytics_dataframe[label].mean()), 2)
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

    st.markdown("### Scored Dataset Summary")
    summary_columns = [
        "Participant",
        "Name",
        "Subject",
        "Task",
        "Category",
        "Total Score",
        "Percentage",
    ]
    st.dataframe(
        analytics_dataframe[summary_columns],
        hide_index=True,
        use_container_width=True,
        column_config={
            "Participant": st.column_config.TextColumn("Participant Code"),
            "Subject": st.column_config.TextColumn("Pedagogy Subject", width="large"),
            "Category": st.column_config.TextColumn("Task Category", width="large"),
            "Percentage": st.column_config.NumberColumn(
                "Percentage (%)", format="%.2f"
            ),
        },
    )

    with st.expander("View Complete Dimension-Wise Dataset"):
        st.dataframe(
            analytics_dataframe,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Percentage": st.column_config.NumberColumn(
                    "Percentage (%)", format="%.2f"
                )
            },
        )


# =======================================================
# DOWNLOAD DATA PAGE
# =======================================================


def render_download_data() -> None:
    st.title("Download Data")

    if not require_approved_access():
        return

    try:
        submissions = fetch_all_submissions()
    except Exception as exc:
        st.error(f"Data could not be retrieved: {clean_error_message(exc)}")
        return

    if not submissions:
        st.warning("No responses are available for download.")
        return

    st.download_button(
        "Download Complete Submission Data as CSV",
        data=submissions_to_csv(submissions),
        file_name=(
            "VoiceBridge_PST_Submissions_and_Scores_"
            f'{datetime.now(IST).strftime("%Y%m%d_%H%M")}.csv'
        ),
        mime="text/csv",
        type="primary",
    )

    st.caption(
        "The CSV includes participant details, task information, written "
        "responses, reflections, rubric scores, total score, percentage, teacher "
        "feedback, and audio-file metadata. Download individual recordings from "
        "Review Responses."
    )

    preview_dataframe = pd.DataFrame(
        [
            {
                "Participant": row.get("student_id"),
                "Name": row.get("participant_name"),
                "Subject": row.get("pedagogy_subject"),
                "Task": row.get("task_id"),
                "Submitted": format_datetime(row.get("submitted_at")),
                "Scored": "Yes" if is_scored(row) else "No",
                "Total Score": row.get("total_score"),
                "Percentage": (
                    round(float(row.get("percentage")), 2)
                    if row.get("percentage") is not None
                    else None
                ),
                "Reference": row.get("submission_reference"),
            }
            for row in submissions
        ]
    )

    st.markdown("### Data Preview")
    st.dataframe(
        preview_dataframe,
        hide_index=True,
        use_container_width=True,
        column_order=[
            "Participant",
            "Name",
            "Subject",
            "Task",
            "Submitted",
            "Scored",
            "Total Score",
            "Percentage",
            "Reference",
        ],
        column_config={
            "Subject": st.column_config.TextColumn("Pedagogy Subject", width="large"),
            "Reference": st.column_config.TextColumn(
                "Submission Reference", width="large"
            ),
            "Percentage": st.column_config.NumberColumn(
                "Percentage (%)", format="%.2f"
            ),
        },
    )

# =======================================================
# SIDEBAR AND ROUTING
# =======================================================

st.sidebar.markdown(f"## {MIC_ICON} VoiceBridge-PST")
st.sidebar.caption("Activity and Analytics Platform")

current_profile = get_current_profile(silent=True) if is_logged_in() else None

if current_profile is None:
    navigation_options = [
        "Home",
        "Activity Submission",
        "Teacher-Educator Login",
        "Create Teacher Account",
    ]
elif has_approved_teacher_access(current_profile):
    navigation_options = [
        "Home",
        "Activity Submission",
        "Review Responses",
        "Score Responses",
        "Diagnostic Profile",
        "Task Analytics",
        "Download Data",
        "Account Status",
        "My Account",
    ]
    if is_platform_admin(current_profile):
        navigation_options.append("Admin User Management")
else:
    navigation_options = [
        "Home",
        "Activity Submission",
        "Account Status",
        "My Account",
    ]

page = st.sidebar.radio(
    "Navigation",
    navigation_options,
    key="main_navigation",
)

st.sidebar.divider()

if current_profile:
    st.sidebar.success(
        f'{current_profile.get("full_name", "User")}\n\n'
        f'{str(current_profile.get("account_status", "")).title()}'
    )

    if (
        current_profile.get("role") == "teacher_educator"
        and current_profile.get("account_status") == "approved"
        and current_profile.get("workspace_id")
    ):
        try:
            workspace_response = (
                get_user_client()
                .table("voicebridge_workspaces")
                .select("workspace_name,workspace_code")
                .eq("id", current_profile["workspace_id"])
                .limit(1)
                .execute()
            )
            workspace_rows = list(workspace_response.data or [])
            if workspace_rows:
                workspace = workspace_rows[0]
                st.sidebar.info(
                    f'Workspace: {workspace.get("workspace_name")}\n\n'
                    f'Code: {workspace.get("workspace_code")}'
                )
        except Exception:
            pass

    if st.sidebar.button("Log out", use_container_width=True):
        try:
            get_user_client().auth.sign_out()
        except Exception:
            pass
        clear_auth_state()
        st.rerun()
else:
    st.sidebar.info(
        "Participants submit with a workspace code. Teacher Educators create "
        "individual accounts and require administrator approval."
    )

connected, connection_error = service_connection_status()
if connected:
    st.sidebar.success("Permanent cloud storage connected")
else:
    st.sidebar.error("Permanent storage is not connected.")
    if connection_error:
        st.sidebar.caption(connection_error[:180])

PAGES = {
    "Home": render_home,
    "Activity Submission": render_activity_submission,
    "Teacher-Educator Login": render_teacher_login,
    "Create Teacher Account": render_create_account,
    "Account Status": render_account_status,
    "My Account": render_my_account,
    "Review Responses": render_review_responses,
    "Score Responses": render_score_responses,
    "Diagnostic Profile": render_diagnostic_profile,
    "Task Analytics": render_task_analytics,
    "Download Data": render_download_data,
    "Admin User Management": render_admin_user_management,
}

PAGES[page]()

