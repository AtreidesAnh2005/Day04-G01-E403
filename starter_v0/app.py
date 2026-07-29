from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

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
load_lab_env(ROOT)

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

    /* Main Container & Background */
    .stApp {
        background-color: #faf7fd;
        color: #2e1065;
    }

    /* Header Styling */
    .header-container {
        background: linear-gradient(135deg, #ede7f6 0%, #e1d5f2 50%, #d1c4e9 100%);
        padding: 1.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        border: 1px solid #d8b4fe;
        box-shadow: 0 4px 15px rgba(124, 77, 255, 0.08);
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
        background-color: #f3ebff;
        border-right: 1px solid #e9d5ff;
    }
    [data-testid="stSidebar"] .stMarkdown h1, 
    [data-testid="stSidebar"] .stMarkdown h2, 
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #4c1d95;
    }

    /* Tool Event Trace Cards */
    .tool-trace-card {
        background-color: #ffffff;
        border: 1px solid #e9d5ff;
        border-left: 4px solid #8b5cf6;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 2px 8px rgba(139, 92, 246, 0.05);
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

init_session_state()

# Sidebar: Controls & Artifact Info
with st.sidebar:
    st.image("https://img.icons8.com/isometric/96/purple-crystal.png", width=64)
    st.title("🔮 Agent Control Panel")
    st.caption("Pastel Edition — Research Agent Tool Eval")

    st.markdown("---")
    st.subheader("⚙️ Run Configuration")

    provider_choice = st.selectbox(
        "Model Provider",
        options=["openrouter", "openai", "anthropic", "gemini"],
        index=0,
        help="Select the LLM provider for agent execution",
    )

    version_choice = st.text_input(
        "Artifact Version Label",
        value="v0",
        help="e.g. v0 (baseline), v1, v2, v3 (optimizations)",
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
            Evidence-Driven Agent Evaluation & Tool Execution Loop • Tone Tím Pastel
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Tabs for Main Interface
tab_chat, tab_eval, tab_tools = st.tabs(["💬 Live Agent Chat", "📊 Run Logs & Evidence", "🛠️ Tool Declarations"])

with tab_chat:
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
            with st.spinner("🔮 Agent đang tư duy và gọi tools..."):
                loop_result = run_model_tool_loop(
                    provider=provider,
                    messages=working_messages,
                    tools=openai_tools,
                    model=selected_model,
                    max_tool_rounds=max_tool_rounds,
                )

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
    st.markdown("Xem lại thông số từ các lần chạy eval (`runs/*.json`) và transcript (`transcripts/*.json`).")

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
                    summary = run_content.get("summary", {})

                    st.markdown(
                        f"""
                        <div class="tool-trace-card">
                            <h4 style="margin:0; color:#4c1d95;">Version: <span class="badge badge-purple">{run_content.get('artifact_version', 'N/A')}</span></h4>
                            <hr style="margin:0.5rem 0; border-color:#e9d5ff;"/>
                            <p><strong>Case Accuracy:</strong> <code>{summary.get('case_accuracy', 'N/A')}</code></p>
                            <p><strong>Tool Routing Accuracy:</strong> <code>{summary.get('tool_routing_accuracy', 'N/A')}</code></p>
                            <p><strong>Argument Accuracy:</strong> <code>{summary.get('argument_accuracy', 'N/A')}</code></p>
                            <p><strong>Provider Errors:</strong> <code>{summary.get('provider_error_cases', 0)}</code></p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
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
                    st.markdown(
                        f"""
                        <div class="tool-trace-card">
                            <h4 style="margin:0; color:#4c1d95;">Transcript ID: <span class="badge badge-pink">{tr_content.get('transcript_id', 'N/A')}</span></h4>
                            <p style="font-size:0.85rem; margin-top:0.4rem;"><strong>Turns Count:</strong> {len(tr_content.get('turns', []))}</p>
                            <p style="font-size:0.85rem;"><strong>Artifact Version:</strong> {tr_content.get('artifact_version', 'N/A')}</p>
                        </div>
                        """,
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
    st.markdown("Danh sách các Tool đã khai báo trong `artifacts/tools.yaml` tuân theo tiêu chuẩn **API-CONTRACTS.md**.")

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
