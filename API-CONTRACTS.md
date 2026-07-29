# Agent & Tool Interaction Protocol

## Purpose:
The Research Agent system operates through a structured interaction loop between the User/UI, the LLM Model Provider, and External Tool Execution Services. This document serves as the formal contract for tool declarations, message passing protocols, standard response formats, and evaluation log schemas across all system components.

## Required Contents:

### 1. Tool Declarations & Schema Contracts (tools.yaml & system_prompt.md)
   - Complete list of declared tools (e.g., clarify, timeline, social_search, lookup, fetch, format, send, policy, papers, paper_text, and custom team tools).
   - Parameter schemas for each tool (argument names, data types, required fields, and default values).
   - Tool routing boundaries: Guidance on when tools should be called vs. when requests are out-of-scope or require clarification.

### 2. Agent Loop & Message Passing Flow (chat.py / run_model_tool_loop)
   - Step-by-step multi-turn communication flow:
     (User Request → LLM Decision → Tool Call Trigger → Tool Execution → Tool Result Feedback → Final Agent Response).
   - Message & Event direction (User → Agent → Tool Runner → External API → Tool Runner → Agent → UI).
   - Structure of internal payload objects: `rounds`, `tool_events`, `actual_tool_calls`, and `tool_results`.
   - Confirmation Boundary Protocol: Handling sensitive actions (e.g., `send` via Telegram) and missing information via `clarify(response_type="yes_no" | "text")`.

### 3. Standard Response & Log Schemas
   - Unified Tool Execution Output Schema (Success vs Failure payload structure: `status`, `items`, `data`, `error`, `message`).
   - Unified Transcript & Run Evaluation Schema (`transcripts/*.transcript.json` and `runs/*.json` log structure).
   - Metric tracking format: `case_accuracy`, `tool_routing_accuracy`, `argument_accuracy`, `observed_mismatch`, `failures`.

### 4. Error & Exception Handling
   - Standardized error codes and response structures (Provider Error, Tool API Quota/Timeout, Invalid Arguments, Unregistered Tool).
   - Handling logic when tool execution fails vs. routing fails.
   - Fallback conventions for UI rendering during API errors or missing credentials.
