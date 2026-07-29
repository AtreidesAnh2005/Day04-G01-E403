from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Ensure parent directory (starter_v0) is in sys.path for backend imports
FRONTEND_DIR = Path(__file__).resolve().parent
STARTER_ROOT = FRONTEND_DIR.parent
if str(STARTER_ROOT) not in sys.path:
    sys.path.insert(0, str(STARTER_ROOT))

import streamlit as st

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version
from chat import (
    ROOT,
    ARTIFACTS_DIR,
    now_iso,
    safe_slug,
    trim_history,
    run_model_tool_loop,
    write_transcript,
)

# Load Environment Variables
load_lab_env(STARTER_ROOT)

# Page Configuration & Pastel Purple Theme CSS
st.set_page_config(
    page_title="Research Agent — Tool Execution Eval",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

PASTEL_PURPLE_CSS = """
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    :root {
        --purple-950: #2e1065;
        --purple-700: #6d28d9;
        --purple-500: #8b5cf6;
        --purple-200: #ddd6fe;
        --surface: rgba(255, 255, 255, 0.82);
        --ease-spring: cubic-bezier(.22, 1, .36, 1);
    }

    @keyframes page-enter {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes card-enter {
        from { opacity: 0; transform: translateY(10px) scale(.99); }
        to { opacity: 1; transform: translateY(0) scale(1); }
    }
    @keyframes ambient-drift {
        0%, 100% { transform: translate3d(0, 0, 0) rotate(0deg); }
        50% { transform: translate3d(18px, -14px, 0) rotate(5deg); }
    }
    @keyframes thinking-bounce {
        0%, 60%, 100% { transform: translateY(0); opacity: .42; }
        30% { transform: translateY(-5px); opacity: 1; }
    }
    @keyframes thinking-glow {
        0%, 100% { box-shadow: 0 8px 28px rgba(139, 92, 246, .10); }
        50% { box-shadow: 0 10px 34px rgba(139, 92, 246, .24); }
    }
    @keyframes header-flow {
        0%, 100% { background-position: 0% 50%, 0% 50%; }
        50% { background-position: 100% 50%, 100% 50%; }
    }
    @keyframes header-sheen {
        0% { transform: translateX(-130%) skewX(-18deg); opacity: 0; }
        15% { opacity: .7; }
        45%, 100% { transform: translateX(260%) skewX(-18deg); opacity: 0; }
    }
    @keyframes header-star-float {
        0%, 100% { transform: translateY(-50%) rotate(0deg) scale(1); opacity: .14; }
        50% { transform: translateY(-58%) rotate(12deg) scale(1.08); opacity: .24; }
    }

    /* Main Container & Background */
    .stApp {
        background:
            radial-gradient(circle at 8% 10%, rgba(196, 181, 253, .34), transparent 22rem),
            radial-gradient(circle at 50% 6%, rgba(165, 243, 252, .22), transparent 24rem),
            radial-gradient(circle at 88% 16%, rgba(251, 207, 232, .30), transparent 23rem),
            radial-gradient(circle at 20% 52%, rgba(186, 230, 253, .20), transparent 25rem),
            radial-gradient(circle at 72% 55%, rgba(221, 214, 254, .32), transparent 28rem),
            radial-gradient(circle at 9% 91%, rgba(254, 215, 170, .20), transparent 22rem),
            radial-gradient(circle at 92% 88%, rgba(153, 246, 228, .18), transparent 25rem),
            linear-gradient(145deg, #fdfcff 0%, #f7f5fb 46%, #fbfaff 100%);
        color: #2e1065;
        isolation: isolate;
    }
    .stApp::before,
    .stApp::after {
        content: "";
        position: fixed;
        z-index: 0;
        pointer-events: none;
        animation: ambient-drift 14s ease-in-out infinite;
    }
    .stApp > * {
        position: relative;
        z-index: 1;
    }
    .stApp::before {
        inset: -30px;
        opacity: .36;
        background-image:
            radial-gradient(circle, rgba(109, 40, 217, .32) 1px, transparent 1.5px),
            linear-gradient(30deg, transparent 48.8%, rgba(99, 102, 241, .09) 49%, rgba(99, 102, 241, .09) 51%, transparent 51.2%),
            linear-gradient(150deg, transparent 48.8%, rgba(6, 182, 212, .07) 49%, rgba(6, 182, 212, .07) 51%, transparent 51.2%);
        background-size: 30px 30px, 120px 208px, 120px 208px;
        background-position: 0 0, 0 0, 60px 104px;
        mask-image: linear-gradient(to bottom, rgba(0,0,0,.9), rgba(0,0,0,.55));
        -webkit-mask-image: linear-gradient(to bottom, rgba(0,0,0,.9), rgba(0,0,0,.55));
    }
    .stApp::after {
        inset: -30px;
        opacity: .55;
        background:
            radial-gradient(circle at 15% 28%, rgba(255,255,255,.90) 0 3px, transparent 4px),
            radial-gradient(circle at 82% 38%, rgba(124,58,237,.24) 0 2px, transparent 3px),
            radial-gradient(circle at 42% 76%, rgba(8,145,178,.20) 0 2px, transparent 3px),
            radial-gradient(circle at 90% 84%, rgba(244,114,182,.20) 0 3px, transparent 4px);
        background-size: 180px 180px, 230px 230px, 270px 270px, 320px 320px;
        animation-delay: -7s;
    }

    /* Prevent Top Streamlit Header Bar from covering the first block */
    .main .block-container, [data-testid="stMain"] .block-container, .block-container {
        padding-top: 4.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1400px;
        animation: page-enter .42s var(--ease-spring) both;
    }

    [data-testid="stHeader"] {
        background-color: rgba(250, 247, 253, 0.94) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border-bottom: 1px solid rgba(216, 180, 254, 0.4) !important;
        z-index: 999 !important;
    }
    [data-testid="stHeader"] * {
        color: #4a148c !important;
    }

    @media (prefers-color-scheme: dark) {
        [data-testid="stHeader"] {
            background-color: rgba(15, 8, 29, 0.94) !important;
            border-bottom: 1px solid rgba(91, 33, 182, 0.5) !important;
        }
        [data-testid="stHeader"] * {
            color: #f3e8ff !important;
        }
    }

    /* Header Styling */
    [data-testid="stElementContainer"]:has(> .stMarkdown .header-container) {
        position: relative;
        z-index: 100;
        isolation: isolate;
    }
    .header-container {
        background:
            linear-gradient(120deg, rgba(255,255,255,.68), rgba(237,233,254,.78)),
            linear-gradient(115deg, #ede9fe 0%, #cffafe 32%, #fce7f3 68%, #ddd6fe 100%);
        background-size: 220% 220%, 240% 240%;
        padding: 1.5rem 2rem;
        border-radius: 16px;
        margin-top: 0.5rem;
        margin-bottom: 1.2rem;
        border: 1px solid #d8b4fe;
        box-shadow: 0 14px 38px rgba(76, 29, 149, .10), inset 0 1px 0 rgba(255,255,255,.72);
        backdrop-filter: blur(18px) saturate(120%);
        -webkit-backdrop-filter: blur(18px) saturate(120%);
        position: relative;
        overflow: hidden;
        animation:
            page-enter .55s var(--ease-spring) both,
            header-flow 10s ease-in-out infinite .55s;
        transition: box-shadow .25s ease, border-color .25s ease;
    }
    .header-container::before {
        content: "";
        position: absolute;
        z-index: 1;
        top: -35%;
        bottom: -35%;
        left: 0;
        width: 22%;
        pointer-events: none;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,.55), transparent);
        filter: blur(3px);
        animation: header-sheen 7s ease-in-out infinite 1.2s;
    }
    .header-container::after {
        content: "✦";
        position: absolute;
        right: 1.6rem;
        top: 50%;
        transform: translateY(-50%);
        color: rgba(109, 40, 217, .16);
        font-size: 5rem;
        line-height: 1;
        pointer-events: none;
        animation: header-star-float 5s ease-in-out infinite;
    }
    .header-container > * {
        position: relative;
        z-index: 2;
    }
    .header-title {
        color: #4a148c;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .header-subtitle {
        color: #6a1b9a;
        font-size: 0.95rem;
        margin-top: 0.4rem;
        font-weight: 500;
    }
    .hero-badge-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.8rem;
    }
    .info-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.3rem 0.6rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
        background-color: rgba(255,255,255,0.7);
        color: #6b21a8;
        border: 1px solid #e9d5ff;
        transition: transform .24s var(--ease-spring), background-color .24s ease, box-shadow .24s ease;
    }
    .header-container .info-pill:hover {
        transform: translateY(-2px);
        background-color: rgba(255,255,255,.90);
        box-shadow: 0 6px 18px rgba(109,40,217,.12);
    }
    .empty-state-card, .section-card {
        background: linear-gradient(135deg, rgba(255,255,255,.88) 0%, rgba(252,250,255,.74) 100%);
        border: 1px solid #e9d5ff;
        border-radius: 14px;
        padding: 1rem 1.1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px rgba(139, 92, 246, 0.05);
        animation: card-enter .45s var(--ease-spring) both;
        transition: transform .25s var(--ease-spring), box-shadow .25s ease, border-color .25s ease;
        backdrop-filter: blur(14px) saturate(115%);
        -webkit-backdrop-filter: blur(14px) saturate(115%);
    }
    .empty-state-card:hover, .section-card:hover {
        transform: translateY(-2px);
        border-color: #d8b4fe;
        box-shadow: 0 10px 28px rgba(109, 40, 217, .10);
    }
    .empty-state-title, .section-card-title {
        font-size: 1rem;
        font-weight: 700;
        color: #4c1d95;
        margin-bottom: 0.35rem;
    }
    .empty-state-body, .section-card-body {
        color: #6b21a8;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #fcfaff 100%);
        border: 1px solid #e9d5ff;
        border-radius: 12px;
        padding: 0.8rem 0.9rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 2px 8px rgba(139, 92, 246, 0.05);
    }

    @media (max-width: 900px) {
        [data-testid="stElementContainer"]:has(> .stMarkdown .header-container) {
            top: .35rem;
        }
        .header-container {
            padding: .85rem 1rem;
            margin-bottom: .75rem;
            border-radius: 14px;
        }
        .header-title {
            font-size: 1.35rem;
        }
        .header-subtitle {
            margin-top: .2rem;
            font-size: .82rem;
        }
        .hero-badge-row {
            display: none;
        }
        .section-card, .empty-state-card {
            padding: 0.85rem 0.95rem;
        }
    }

    /* Version Badges */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 8px;
        font-size: 0.8rem;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }
    .badge-purple {
        background-color: #e9d5ff;
        color: #581c87;
        border: 1px solid #c084fc;
    }
    .badge-pink {
        background-color: #fbcfe8;
        color: #831843;
        border: 1px solid #f472b6;
    }
    .badge-slate {
        background-color: #f1f5f9;
        color: #334155;
        border: 1px solid #cbd5e1;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(246,241,255,.90), rgba(240,249,255,.82));
        border-right: 1px solid #e9d5ff;
        backdrop-filter: blur(18px) saturate(120%);
        -webkit-backdrop-filter: blur(18px) saturate(120%);
    }
    [data-testid="stSidebar"] .stMarkdown h1, 
    [data-testid="stSidebar"] .stMarkdown h2, 
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #4c1d95;
    }

    /* Tool Event Trace Cards */
    .tool-trace-card {
        background: rgba(255, 255, 255, .82);
        border: 1px solid #e9d5ff;
        border-left: 4px solid #8b5cf6;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 2px 8px rgba(139, 92, 246, 0.05);
        animation: card-enter .38s var(--ease-spring) both;
        transition: transform .22s var(--ease-spring), box-shadow .22s ease;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
    }
    .tool-trace-card:hover {
        transform: translateX(3px);
        box-shadow: 0 7px 20px rgba(109, 40, 217, .11);
    }
    .tool-trace-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-weight: 600;
        color: #581c87;
        margin-bottom: 0.4rem;
    }
    .tool-name-tag {
        background-color: #f3e8ff;
        color: #6b21a8;
        padding: 0.2rem 0.5rem;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
    }

    /* Clarification Banner */
    .clarification-banner {
        background-color: #fff1f2;
        border: 1px solid #fecdd3;
        border-left: 4px solid #f43f5e;
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        color: #881337;
    }

    /* Custom Buttons */
    .stButton>button {
        background-color: #8b5cf6;
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #7c3aed;
        box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
        color: white;
        transform: translateY(-1px);
    }
    .stButton>button:active {
        transform: translateY(0) scale(.98);
    }

    /* Smooth tab and chat transitions */
    [data-testid="stTabs"] [role="tab"] {
        transition: color .2s ease, background-color .2s ease, transform .2s var(--ease-spring);
    }
    [data-testid="stTabs"] [role="tab"]:hover { transform: translateY(-1px); }
    [data-testid="stTabs"] [role="tabpanel"] { animation: page-enter .38s var(--ease-spring) both; }
    [data-testid="stChatMessage"] {
        animation: card-enter .42s var(--ease-spring) both;
        border-radius: 16px;
        transition: background-color .2s ease, box-shadow .2s ease;
    }
    [data-testid="stChatMessage"]:hover {
        background: rgba(255, 255, 255, .42);
        box-shadow: 0 8px 24px rgba(109, 40, 217, .06);
    }

    /* Branded thinking state */
    .thinking-shell {
        display: inline-flex;
        align-items: center;
        gap: .7rem;
        padding: .72rem 1rem;
        margin: .2rem 0 .65rem;
        color: #5b21b6;
        background: linear-gradient(110deg, rgba(255,255,255,.88), rgba(245,243,255,.92));
        border: 1px solid #ddd6fe;
        border-radius: 999px;
        font-size: .9rem;
        font-weight: 600;
        animation: card-enter .3s var(--ease-spring) both, thinking-glow 2.2s ease-in-out infinite;
    }
    .thinking-orb {
        width: 1.65rem;
        height: 1.65rem;
        display: grid;
        place-items: center;
        border-radius: 50%;
        color: white;
        background: linear-gradient(135deg, #a78bfa, #7c3aed);
    }
    .thinking-dots { display: inline-flex; gap: .22rem; margin-left: .1rem; }
    .thinking-dots i {
        width: .32rem;
        height: .32rem;
        border-radius: 50%;
        background: #8b5cf6;
        animation: thinking-bounce 1.2s ease-in-out infinite;
    }
    .thinking-dots i:nth-child(2) { animation-delay: .15s; }
    .thinking-dots i:nth-child(3) { animation-delay: .30s; }

    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation-duration: .01ms !important;
            animation-iteration-count: 1 !important;
            scroll-behavior: auto !important;
            transition-duration: .01ms !important;
        }
    }

    /* Accordion Custom Styling */
    .stMarkdown code {
        font-family: 'JetBrains Mono', monospace;
        background-color: #f5f3ff;
        color: #6b21a8;
    }
</style>
"""

st.markdown(PASTEL_PURPLE_CSS, unsafe_allow_html=True)


# Initialize Session State
def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "history" not in st.session_state:
        st.session_state.history = []
    if "transcript_turns" not in st.session_state:
        st.session_state.transcript_turns = []
    if "transcript_id" not in st.session_state:
        st.session_state.transcript_id = None
    if "transcript_path" not in st.session_state:
        st.session_state.transcript_path = None
    if "awaiting_clarification" not in st.session_state:
        st.session_state.awaiting_clarification = False


def metric_percent(value: Any) -> str:
    try:
        return f"{float(value):.1%}"
    except (TypeError, ValueError):
        return str(value)


def build_run_metrics(run_content: dict[str, Any]) -> dict[str, Any]:
    summary = run_content.get("summary", {})
    return {
        "case_accuracy": float(summary.get("case_accuracy", 0) or 0),
        "tool_routing_accuracy": float(summary.get("tool_routing_accuracy", 0) or 0),
        "argument_accuracy": float(summary.get("argument_accuracy", 0) or 0),
        "provider_error_cases": int(summary.get("provider_error_cases", 0) or 0),
        "failure_counts": summary.get("failure_counts", {}),
    }


init_session_state()

# Sidebar: Controls & Artifact Info
with st.sidebar:
    st.title("🔮 Agent Control Panel")
    st.caption("Pastel Edition — Research Agent Tool Eval")

    st.markdown("---")
    st.subheader("⚙️ Run Configuration")

    provider_choice = st.selectbox(
        "Model Provider",
        options=["openai"],
        index=0,
        help="Model Provider fixed to OpenAI for this project",
    )

    version_choice = st.selectbox(
        "Artifact Version Label",
        options=["v0", "v1", "v2", "v3"],
        index=0,
        help="Select artifact version label (v0 baseline, v1-v3 optimizations)",
    )

    model_override = st.text_input(
        "Model Override (Optional)",
        value="",
        placeholder="Leave blank for default provider model",
    )

    max_tool_rounds = st.slider(
        "Max Tool Rounds",
        min_value=1,
        max_value=10,
        value=4,
        help="Maximum loop iterations per query",
    )

    history_window = st.number_input(
        "History Context Window",
        min_value=1,
        max_value=20,
        value=5,
        help="Number of past turns kept in LLM context",
    )

    st.markdown("---")
    st.subheader("📜 Artifact Metadata")

    version_dir = ARTIFACTS_DIR / "versions" / version_choice
    if (version_dir / "system_prompt.md").exists() and (version_dir / "tools.yaml").exists():
        sys_prompt_path = version_dir / "system_prompt.md"
        tools_path = version_dir / "tools.yaml"
    else:
        sys_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
        tools_path = ARTIFACTS_DIR / "tools.yaml"

    if sys_prompt_path.exists() and tools_path.exists():
        art_ver = build_artifact_version(version_choice, sys_prompt_path, tools_path)
        st.markdown(f"**Artifact Version:** `{art_ver.artifact_version}`")
        st.markdown(f"**Prompt Hash:** `{art_ver.prompt_hash[:12]}`")
        st.markdown(f"**Tools Hash:** `{art_ver.tools_hash[:12]}`")
    else:
        st.error("Missing system_prompt.md or tools.yaml in artifacts/")


    st.markdown("---")

    if st.button("🗑️ Reset Chat Session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.history = []
        st.session_state.transcript_turns = []
        st.session_state.transcript_id = None
        st.session_state.transcript_path = None
        st.session_state.awaiting_clarification = False
        st.rerun()

# Header Area
st.markdown(
    """
    <div class="header-container">
        <div class="header-title">
            <span>🔮 Research Agent Tool Eval Studio</span>
        </div>
        <div class="header-subtitle">
            Evidence-Driven Agent Evaluation & Tool Execution Loop 
        </div>
        <div class="hero-badge-row">
            <span class="info-pill">💬 Live agent chat</span>
            <span class="info-pill">📊 Evidence inspection</span>
            <span class="info-pill">🛠️ Tool declaration review</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Tabs for Main Interface
tab_chat, tab_eval, tab_tools = st.tabs(["💬 Live Agent Chat", "📊 Run Logs & Evidence", "🛠️ Tool Declarations"])

with tab_chat:
    if not st.session_state.messages:
        st.markdown(
            """
            <div class="empty-state-card">
                <div class="empty-state-title">Start a research workflow</div>
                <div class="empty-state-body">
                    Ask the agent a question, then inspect the tool execution trace and saved transcript in the same session.
                </div>
                <div class="hero-badge-row">
                    <span class="info-pill">Example: Find recent papers about multi-agent systems</span>
                    <span class="info-pill">Example: Compare tool usage across two research prompts</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Render Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🔮"):
            st.markdown(msg["content"])
            
            # If assistant message has tool execution traces, render according to API-CONTRACTS.md
            if msg["role"] == "assistant" and msg.get("tool_events"):
                with st.expander(f"🔧 Tool Execution Trace ({len(msg['tool_events'])} calls)", expanded=False):
                    for idx, event in enumerate(msg["tool_events"], 1):
                        tool_name = event.get("tool", "unknown")
                        tool_args = event.get("args", {})
                        tool_result = event.get("result", {})
                        is_error = "error" in tool_result if isinstance(tool_result, dict) else False

                        st.markdown(
                            f"""
                            <div class="tool-trace-card">
                                <div class="tool-trace-header">
                                    <span class="tool-name-tag">#{idx} {tool_name}</span>
                                    <span class="badge {'badge-pink' if is_error else 'badge-purple'}">
                                        {'ERROR' if is_error else 'OK'}
                                    </span>
                                </div>
                                <div style="font-size:0.85rem; margin-top:0.4rem;">
                                    <strong>Arguments:</strong> <code>{json.dumps(tool_args, ensure_ascii=False)}</code>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        st.json(tool_result, expanded=False)

    # Clarification Notice if waiting for user input
    if st.session_state.awaiting_clarification:
        st.markdown(
            """
            <div class="clarification-banner">
                <strong>💡 Waiting for User Clarification / Confirmation</strong><br/>
                Agent đã gọi tool clarify để nhận thêm chi tiết hoặc xác nhận từ bạn trước khi thực hiện hành động.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Chat Input
    if user_input := st.chat_input("Nhập câu hỏi hoặc yêu cầu nghiên cứu của bạn..."):
        # Display User Message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        # Prepare Engine Setup
        system_prompt = sys_prompt_path.read_text(encoding="utf-8")
        tool_declarations = load_tool_declarations(tools_path)
        openai_tools = to_openai_tools(tool_declarations)

        try:
            provider = make_provider(provider_choice)
        except Exception as exc:
            st.error(f"❌ Failed to load provider '{provider_choice}': {exc}")
            st.stop()

        selected_model = model_override if model_override.strip() else getattr(provider, "default_model", None)
        art_ver = build_artifact_version(version_choice, sys_prompt_path, tools_path)

        # Initialize Transcript if new session
        if st.session_state.transcript_id is None:
            timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
            t_id = f"{safe_slug(version_choice)}_{safe_slug(provider_choice)}_{timestamp}"
            t_path = ROOT / "transcripts" / f"{t_id}.transcript.json"
            st.session_state.transcript_id = t_id
            st.session_state.transcript_path = t_path

        # Build working messages for LLM
        system_prompt_msg = {"role": "system", "content": system_prompt}
        trimmed_ctx = trim_history(st.session_state.history, history_window)
        working_messages = [system_prompt_msg] + trimmed_ctx + [{"role": "user", "content": user_input}]

        # Execute Agent Tool Loop
        with st.chat_message("assistant", avatar="🔮"):
            thinking_placeholder = st.empty()
            thinking_placeholder.markdown(
                """
                <div class="thinking-shell" role="status" aria-live="polite">
                    <span class="thinking-orb">✦</span>
                    <span>Agent đang phân tích và chọn công cụ</span>
                    <span class="thinking-dots" aria-hidden="true"><i></i><i></i><i></i></span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            try:
                loop_result = run_model_tool_loop(
                    provider=provider,
                    messages=working_messages,
                    tools=openai_tools,
                    model=selected_model,
                    max_tool_rounds=max_tool_rounds,
                )
            finally:
                thinking_placeholder.empty()

            status = loop_result.get("status")
            assistant_text = loop_result.get("assistant_text", "")
            tool_events = loop_result.get("tool_events", [])
            rounds = loop_result.get("rounds", [])

            st.markdown(assistant_text)

            if tool_events:
                with st.expander(f"🔧 Tool Execution Trace ({len(tool_events)} calls)", expanded=True):
                    for idx, event in enumerate(tool_events, 1):
                        tool_name = event.get("tool", "unknown")
                        tool_args = event.get("args", {})
                        tool_result = event.get("result", {})
                        is_error = "error" in tool_result if isinstance(tool_result, dict) else False

                        st.markdown(
                            f"""
                            <div class="tool-trace-card">
                                <div class="tool-trace-header">
                                    <span class="tool-name-tag">#{idx} {tool_name}</span>
                                    <span class="badge {'badge-pink' if is_error else 'badge-purple'}">
                                        {'ERROR' if is_error else 'OK'}
                                    </span>
                                </div>
                                <div style="font-size:0.85rem; margin-top:0.4rem;">
                                    <strong>Arguments:</strong> <code>{json.dumps(tool_args, ensure_ascii=False)}</code>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        st.json(tool_result, expanded=False)

        # Update Session State History
        st.session_state.messages.append({
            "role": "assistant",
            "content": assistant_text,
            "tool_events": tool_events,
            "status": status,
        })
        st.session_state.history.append({"role": "user", "content": user_input})
        st.session_state.history.append({"role": "assistant", "content": assistant_text})
        st.session_state.awaiting_clarification = (status == "waiting_for_user")

        # Save Transcript
        turn_index = len(st.session_state.transcript_turns) + 1
        turn_record = {
            "turn_index": turn_index,
            "user_text": user_input,
            "status": status,
            "assistant_text": assistant_text,
            "rounds": rounds,
            "tool_events": tool_events,
            "timestamp": now_iso(),
        }
        st.session_state.transcript_turns.append(turn_record)

        transcript_data = {
            "transcript_id": st.session_state.transcript_id,
            **artifact_version_dict(art_ver),
            "provider": provider_choice,
            "model": selected_model,
            "system_prompt": str(sys_prompt_path),
            "tools": str(tools_path),
            "history_window": history_window,
            "max_tool_rounds": max_tool_rounds,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "turns": st.session_state.transcript_turns,
        }
        write_transcript(st.session_state.transcript_path, transcript_data)
        st.toast("✅ Transcript saved successfully", icon="💾")

# Tab 2: Run Logs & Evidence Inspector
with tab_eval:
    st.subheader("📊 Evaluation Evidence Inspector")
    st.markdown(
        """
        <div class="section-card">
            <div class="section-card-title">Evidence overview</div>
            <div class="section-card-body">
                Review benchmark runs and chat transcripts side by side to compare performance, agent behavior, and tool traces.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    runs_dir = ROOT / "runs"
    transcripts_dir = ROOT / "transcripts"

    col_run, col_tr = st.columns(2)

    with col_run:
        st.markdown("### 🏃 Benchmark Runs (`runs/`)")
        run_files = sorted(runs_dir.glob("*.json")) if runs_dir.exists() else []
        if run_files:
            selected_run_file = st.selectbox("Select Run Log", options=run_files, format_func=lambda x: x.name)
            if selected_run_file:
                try:
                    run_content = json.loads(selected_run_file.read_text(encoding="utf-8"))
                    run_metrics = build_run_metrics(run_content)

                    st.markdown(
                        f"""
                        <div class="tool-trace-card">
                            <h4 style="margin:0; color:#4c1d95;">Version: <span class="badge badge-purple">{run_content.get('artifact_version', 'N/A')}</span></h4>
                            <p style="font-size:0.85rem; margin-top:0.4rem; color:#6b21a8;">{run_content.get('description', 'Benchmark summary')}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
                    mcol1.metric("Case Accuracy", metric_percent(run_metrics["case_accuracy"]))
                    mcol2.metric("Tool Routing", metric_percent(run_metrics["tool_routing_accuracy"]))
                    mcol3.metric("Argument Accuracy", metric_percent(run_metrics["argument_accuracy"]))
                    mcol4.metric("Provider Errors", run_metrics["provider_error_cases"])

                    chart_data = {
                        "Metric": ["Case", "Routing", "Argument"],
                        "Score": [
                            run_metrics["case_accuracy"],
                            run_metrics["tool_routing_accuracy"],
                            run_metrics["argument_accuracy"],
                        ],
                    }
                    st.bar_chart(chart_data, x="Metric", y="Score")

                    failure_counts = run_metrics["failure_counts"]
                    if failure_counts:
                        failure_items = [(k, v) for k, v in failure_counts.items() if v]
                        if failure_items:
                            fail_data = {"Failure Type": [k for k, _ in failure_items], "Count": [v for _, v in failure_items]}
                            st.caption("Failure breakdown")
                            st.bar_chart(fail_data, x="Failure Type", y="Count")

                    with st.expander("📄 Full Run Log JSON"):
                        st.json(run_content)
                except Exception as e:
                    st.error(f"Error reading run file: {e}")
        else:
            st.info("No run logs found in `runs/`.")

    with col_tr:
        st.markdown("### 📝 Chat Transcripts (`transcripts/`)")
        tr_files = sorted(transcripts_dir.glob("*.json")) if transcripts_dir.exists() else []
        if tr_files:
            selected_tr_file = st.selectbox("Select Transcript Log", options=tr_files, format_func=lambda x: x.name)
            if selected_tr_file:
                try:
                    tr_content = json.loads(selected_tr_file.read_text(encoding="utf-8"))
                    turns = tr_content.get("turns", [])
                    st.markdown(
                        f"""
                        <div class="tool-trace-card">
                            <h4 style="margin:0; color:#4c1d95;">Transcript ID: <span class="badge badge-pink">{tr_content.get('transcript_id', 'N/A')}</span></h4>
                            <p style="font-size:0.85rem; margin-top:0.4rem;"><strong>Turns Count:</strong> {len(turns)}</p>
                            <p style="font-size:0.85rem;"><strong>Artifact Version:</strong> {tr_content.get('artifact_version', 'N/A')}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if turns:
                        st.caption("Recent interaction preview")
                        for idx, turn in enumerate(turns[:3], 1):
                            user_text = turn.get("user") or turn.get("user_text") or ""
                            status = turn.get("status") or "unknown"
                            st.markdown(
                                f"<div class='metric-card'><strong>{idx}. {status}</strong><br/>{user_text}</div>",
                                unsafe_allow_html=True,
                            )

                    with st.expander("📄 Full Transcript JSON"):
                        st.json(tr_content)
                except Exception as e:
                    st.error(f"Error reading transcript file: {e}")
        else:
            st.info("No transcript logs found in `transcripts/`.")

# Tab 3: Tool Declarations Viewer
with tab_tools:
    st.subheader("🛠️ Active Tool Declarations")
    st.markdown(
        """
        <div class="section-card">
            <div class="section-card-title">Tool inventory</div>
            <div class="section-card-body">
                Browse the active tool schema and quickly inspect each declaration, its parameters, and its purpose.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if tools_path.exists():
        t_decls = load_tool_declarations(tools_path)
        for tool_item in t_decls:
            t_name = tool_item.get("name")
            t_desc = tool_item.get("description")
            t_params = tool_item.get("parameters", {})

            with st.expander(f"🔧 Tool: `{t_name}`", expanded=False):
                st.write(f"**Description:** {t_desc}")
                st.write("**Parameters Schema:**")
                st.json(t_params)
    else:
        st.error("artifacts/tools.yaml not found.")
