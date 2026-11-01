# Local research records

Install the research-tools package from the configuration checkout before using its CLI. Commands consume one JSON object on stdin; use a reviewed input file or a quoted heredoc, never untrusted shell interpolation. State is stored under `$XDG_STATE_HOME/opencode-research` (default `~/.local/state/opencode-research`), or the explicit `OPENCODE_RESEARCH_STATE_DIR`. It is private local SQLite state, not Git-tracked research data. Configure these variables for the OpenCode backend in OpenChamber General Environment settings.

`opencode-research-tools doctor` performs no network calls.

`opencode-research-tools run` supports:

- `{"operation":"create","kind":"research","question":"Your question","scope":{"inclusion":[],"exclusion":[],"providers":[]}}`
- `{"operation":"list","kind":"research"}`
- `{"operation":"get","run_id":"RETURNED_ID"}`
- `{"operation":"update","run_id":"RETURNED_ID","expected_revision":0,"action":"transition","payload":{"state":"running"}}`
- `{"operation":"export","run_id":"RETURNED_ID"}` returns JSON, Markdown and evidence CSV as data. It does not write files automatically.

Always use the revision returned by the most recent update. Updates are transactional and reject stale revisions. The update actions are:

| Action | Payload |
| --- | --- |
| evidence | title, provider, url; optional doi, access (metadata/abstract/fulltext), passage, locator, limitations, retrieved_utc |
| query | provider, query; optional search parameters and retrieval metadata |
| screen | evidence_id, decision (include/exclude/uncertain), reason |
| job | provider, job_id, status; optional limits and usage |
| report | text, evidence_ids (existing IDs); optional caveats |
| transition | state |

Evidence additions return a generated evidence ID; duplicate DOI/URL entries are rejected. Reports must refer to existing evidence IDs. Completion requires a nonempty report and evidence inventory, but cannot establish claim validity. Evidence timestamps default to the record time; use the actual retrieval date when it differs. Do not mark a source as read unless actually accessed.

States: planned → running/cancelled; running → paused/awaiting_approval/completed/failed/cancelled; paused/awaiting_approval/failed → running/cancelled. Completed/cancelled runs are immutable. Create follow-up runs instead of overwriting history. Database revisions prevent lost updates. Review the data before saving sensitive material.

Optional OpenAI request: `{"operation":"start","question":"Reviewed question","approve_spend":true,"max_output_tokens":4000}`. Both model and API key must be configured in the backend environment; no model is bundled. Output-token limits are not a full spending cap. Save the returned response ID immediately with a job update. Resume with `{"operation":"retrieve","response_id":"RETURNED_RESPONSE_ID"}`. Preserve output text, citation annotations and usage. No automatic retry occurs after a timeout: check the provider dashboard for an ambiguous submission. Local cancellation never cancels external execution. Retention depends on your OpenAI project and background-mode settings.
