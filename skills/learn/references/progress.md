# Optional learning progress

Use `opencode-research-tools run` with JSON stdin only after the learner opts into local saving. It uses the same private state directory as research runs.

Create: `{"operation":"create","kind":"learning","question":"Understand enzyme kinetics","scope":{"level":"beginner"}}`.

Record an attempt: `{"operation":"update","run_id":"RETURNED_ID","expected_revision":0,"action":"attempt","payload":{"question":"What does Km describe?","response":"Learner answer","feedback":"Qualitative feedback","review_topics":["Km interpretation"]}}`.

For an objective question, optionally include `correct_answer`. The helper compares normalized case and surrounding whitespace and labels its grading method. This is not semantic grading. Do not use exact-text scoring for open questions. No learner response or correct answer is fabricated.

Get/list/export and state transitions use the research-run API documented in the deep-research skill. Export produces a local record and Markdown content, with no implicit publication or remote sync. Resume a lesson by loading its actual run ID. Never infer mastery from the number of attempts. Create a new run for a new lesson after completion.
