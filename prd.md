Technical Requirements Document (TRD)

Project: Agentic AI Code Reviewer — Web Application MVP
Version: Draft 1.0

1. Project Overview & Scope

Objective:
Build a web application that allows developers to authenticate, connect their GitHub (or upload code directly), trigger an AI-powered code review on a repository or PR, and receive actionable results with inline navigation, autofix options, and the ability to merge changes via the app.

Primary users:

Developers: run reviews on personal repos, upload ZIPs, test autofix.

Tech leads/reviewers: view prioritized findings and approve autofixes.

Engineering managers: track review quality and developer adoption (light analytics in future).

In-scope (MVP)

User auth: GitHub OAuth 2.0.

Repo ingest:

Connect GitHub repo via OAuth → clone into sandbox.

Paste repo URL (public) or upload ZIP (private/local testing).

Review flow:

“Start Review” → processing pipeline.

Show progress/status (Queued → Analyzing → Generating Suggestions → Complete).

Results UI:

File/diff navigation.

Inline findings with severity + confidence.

“Why?” → reasoning/explanation modal.

Autofix:

One-click apply safe fixes (style/lint).

Create new PR or commit to branch (GitHub API).

Merge request support:

For verified patches: app creates merge request / PR to main branch with autofix changes.

Audit log:

Per review run: store repo ID, findings, patches, sandbox results.

Out-of-scope (MVP)

Multi-language support beyond Python and JS/TS.

Enterprise org dashboards & long-term analytics.

IDE integrations (deferred).

Full dependency scanning (only Semgrep subset).

2. System Architecture
Core flow

Frontend ↔ Backend API ↔ Agents/Tools ↔ Sandbox ↔ GitHub

Components

Frontend (Next.js/React + Tailwind)

Auth/login, repo selection, review dashboard, file viewer, results pane.

Backend API (FastAPI or Node/Express)

Handles auth sessions, orchestrates LangGraph pipeline, manages jobs, stores results.

LangGraph pipeline (agents as services):

Ingest → Analyzer → Semantic Assistant → Patch Synth → Sandbox → Reporter.

Sandbox execution (Docker/K8s jobs)

Runs lint/tests on candidate patches.

Database (Postgres)

Users, repos, review runs, findings, patches, audit logs.

Object storage (S3/MinIO)

Store logs, artifacts, uploaded repos.

External APIs

GitHub API (clone, PR creation).

LLM API (Semantic Assistant).

3. Detailed End-to-End Workflow
User onboarding

User visits app → logs in via GitHub OAuth.

System fetches repo list (permissions: read/write code, pull requests).

User selects:

Connect Repo (preferred)

or Paste URL (public repo)

or Upload ZIP (for local/private test).

Review run

User clicks “Start Review” on a repo or branch.

Backend:

Clones repo → extracts diff (latest commit or PR branch).

Initializes LangGraph run.

Posts status updates to frontend via WebSocket.

Agents run sequentially:

Analyzer → Semantic Assistant → Patch Synth → Sandbox.

Backend saves results in DB & storage.

Result presentation

Frontend shows status timeline: Queued → Analyzing → Suggestions Ready → Complete.

After completion:

Findings list grouped by severity.

Clickable navigation to file + line context.

“Why?” button expands rationale + tool evidence.

Autofixable findings show “Apply Fix”.

Autofix & Merge

User clicks “Apply Fix”.

Backend applies patch → runs sandbox verification.

If passes → create new branch + PR via GitHub API (or merge request).

UI shows link to created PR.

4. Frontend Requirements
Key Pages / Views

Login Page (GitHub OAuth).

Dashboard (list connected repos, last reviews, status).

Repo Review Page:

Trigger review.

Show progress indicator.

Results tabbed: Summary | Files | Autofixes.

File Viewer (like GitHub diff view):

Inline comments (severity tags, confidence score).

Buttons: Apply Fix / Request Approval / Ignore.

Result Detail Modal:

Rationale, sandbox logs, provenance.

Merge Confirmation Dialog:

PR branch, summary of changes, CTA to open PR on GitHub.

UX priorities

Clarity: Minimal noise, show top issues first.

Actionability: Autofix buttons next to findings.

Trust-building: Sandbox status + tool evidence visible.

Speed: Show progress during processing, even before full results.

5. Backend Requirements
APIs

Auth: GitHub OAuth login, session tokens.

Repo Management: connect repo, list repos, upload ZIP, fetch repo metadata.

Review: start review, poll status, fetch results.

Patch/Autofix: apply patch, run sandbox, create PR.

Logs: fetch audit log for a run.

Processing pipeline

Jobs queued via worker (e.g., Celery/RQ/Sidekiq).

Each review run = pipeline: ingest → analyze → semantic → patch synth → sandbox → report.

Status checkpoints updated in DB, streamed to frontend via WebSocket.

Sandbox

Run ephemeral container with repo + patch applied.

Run linter + pytest or npm test.

Return structured result (pass/fail, logs, duration).

Database Schema (simplified)

Users: id, github_id, email, tokens.

Repos: id, user_id, github_repo_url, type (git/url/upload).

ReviewRuns: id, repo_id, status, started_at, finished_at.

Findings: run_id, file, line, severity, confidence, rationale, tool.

Patches: finding_id, diff, sandbox_result, applied (bool).

6. Autonomous Tooling (MVP)
Tools integrated

GitHub API: repo clone, create branch/PR.

Linters: ESLint, Pyright/Mypy, Flake8/Black.

Formatter: Prettier (JS/TS).

SAST: Semgrep subset.

Test runners: pytest / npm test.

Sandbox runtime: Docker or K8s jobs.

LLM API: for Semantic Assistant.

Tool-calling mechanism

Agents call tools based on pipeline step.

Results inserted into LangGraph state, persisted in DB.

7. Request & Response Lifecycle

Trigger: User clicks Start Review.

Ingest: backend clones repo or unpacks ZIP.

Analyze: static checks + security scan.

LLM reasoning: generate prioritized findings + candidate patches.

Patch synth: produce unified diff.

Sandbox: apply patch, run tests.

Report: save findings, update DB, notify frontend.

UI: user browses findings, applies autofix.

PR creation: backend calls GitHub API → branch + PR created.

End: run archived; results retained 7 days.

8. Scalability & Resilience (MVP)

Single MCP server with job queue.

Stateless frontend + API layer (scale horizontally).

Worker pool for review runs (autoscale).

Sandbox jobs isolated, time- and resource-limited.

Error handling: retry failed steps (max 2 retries).

9. Acceptance Criteria

User can sign up/login with GitHub.

User can connect repo (GitHub), paste URL, or upload ZIP.

User can trigger a review and see progress updates.

After processing, user sees at least:

Top 3 findings with severity/confidence.

File navigation with inline annotations.

Ability to view rationale.

Autofix available for at least 1 class of issue (lint/style).

Sandbox verification runs and returns logs.

User can apply fix → PR created in GitHub.

10. Risks & Mitigations

Repo privacy/data leakage:
Mitigation: process in secure sandbox, minimize data sent to LLM, redact secrets.

False positives:
Mitigation: limit to deterministic tools + high-confidence LLM suggestions.

Sandbox cost & time:
Mitigation: run only small unit tests, apply limits.

Auth complexity:
Mitigation: GitHub OAuth only for MVP, expand later.