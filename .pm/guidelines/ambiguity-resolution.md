---
metadata: {}
---

**Guideline: Ambiguity Resolution**

**Purpose:** To ensure clarity and prevent errors arising from potentially imprecise or approximate information provided in user requests.

**Guideline:**

1.  **Acknowledge Potential Imprecision:** Recognize that user input, especially regarding names (e.g., projects, files, tasks), might be approximate or slightly inaccurate. Do not assume exactness unless the context strongly implies it.
2.  **Verify Before Acting:** If there's ambiguity or a potential mismatch between the user's request and the available data (e.g., a requested project name doesn't exist exactly, but a similar one does), take steps to verify before proceeding with actions based on the potentially incorrect information.
3.  **Verification Methods:**
    - **Listing:** If a specific item (like a project) is requested but not found exactly, list similar or relevant items (e.g., `pm project list`) to help the user identify the correct target.
    - **Clarification:** If listing doesn't resolve the ambiguity, ask a direct clarifying question using `ask_followup_question`, suggesting potential matches.
4.  **Proceed with Confirmation:** Only proceed with the intended action once the correct target or information has been confirmed.