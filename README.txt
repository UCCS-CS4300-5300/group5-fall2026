SPRINT 3 — PROJECT PIPELINE STARTER

Complete assignment, rubric and submission instructions:
https://canvas.uccs.edu/courses/179562/assignments/1115554
Canvas is the authoritative assignment; these files are implementation help.

Deliver a useful, tested project increment; demonstrate its value to a
stakeholder; use this supplied pipeline to verify and deploy it.
The working reporter and reference workflow are provided. You adapt them to
your project; you do not need to build a reporter or write Actions from scratch.

WHEN TO USE THIS ZIP
Use it when you reach CI setup. Add it to your existing project; it is not
a replacement application. Start with this README, then SETUP_REFERENCE.txt
for your platform commands and detailed setup steps. Read TEAM_COMPATIBILITY.txt
first for your current team layout and known setup issues.

CI SETUP CHECKLIST — one team setup, then automatic runs
[ ] 1. Read SETUP_REFERENCE.txt for your Windows/macOS/Codespaces commands.
    Run the supplied offline tests and demo first (8 tests; no network/key).
    Merge the ZIP files at repository root, including project/config/quality_test_settings.py,
    scripts/tests, sample-evidence, quality.coveragerc, requirements-quality.txt
    and .github/workflows/quality.yml
    without overwriting existing work. Synthetic fixtures are not evidence.
[ ] 2. The workflow defaults to Python 3.12 and APP_PATH=core inside project/,
    matching all five teams. Verify these still match your current project.
    Adapt dependency commands, test settings and isolated test database.
    Keep existing versions, dependency manager, lockfile and test runner.
    Use TEAM_COMPATIBILITY.txt for exact install/test commands and Team 3
    JavaScript checks. No requirements-dev.txt is required.
[ ] 3. Confirm a PR runs all app tests plus reporter mocks and collects
    statement/branch coverage, Pylint and Radon into quality-evidence.
    Inspect actual results; retain artifacts even on failure. Failed tests,
    setup/tools or missing evidence must fail. No numeric score targets.
[ ] 4. Set repository variable COURSE_GATEWAY_URL to
    https://sprint3-gateway-1071259812853.us-central1.run.app
    Keep quality.yml, its needs: evidence dependency, successful push-on-main
    condition and report-only id-token permission. No OpenAI key is needed.
    QUALITY_REVIEW_ISSUE_URL is optional; you may link the report from an issue.
[ ] 5. Merge to main; verify the report runs automatically after CI succeeds.
    Download same-run quality-evidence and engineering-quality-report.
    Check their SHA matches your project commit. PRs never call live AI.
[ ] 6. Follow the linked Render + Neon guide. Select After CI Checks Pass.
    Verify deployed SHA, meaningful normal/error behavior and persistence.
    Record one failed check and its fix; confirm it blocked new deployment.
    Review Dependabot alerts. Briefly note project-specific setup adaptations
    in your README, Canvas submission or an optional existing issue; no separate CI essay is required.
[ ] 7. Before tagging, compare the commit ID (SHA) in the passing workflow,
    report and Render deployment with the version you intend to tag. If code
    changes, verify the new version. Issue edits do not change the code.
    See SETUP_REFERENCE.txt step 12 for tag commands. Never move a submitted tag.

WHAT RUNS AUTOMATICALLY AFTER SETUP?
PR -> full CI and mocked reporter tests -> evidence and pass/fail.
Main push -> full CI passes -> automatic AI report -> checks pass -> Render.
A failure stays visible; preserve evidence and fix it without bypassing checks.

QUALITY METRICS — what the results mean
- Statement coverage: percentage of executable statements exercised by tests.
- Branch coverage: percentage of decision branches exercised. Coverage shows
  what ran, not whether the assertions would catch a bug.
- Pylint findings and score: possible errors and maintainability/style concerns;
  inspect the messages, not just the overall score.
- Radon cyclomatic complexity: decision-path complexity of functions; higher
  values suggest code that may need closer review and more focused tests.
- Radon maintainability index: a combined indicator of code maintainability;
  use it as a clue, not proof that code is good or bad.
- Focused mutmut results (once before submission): whether tests detect small
  deliberate changes to selected business logic. Killed means detected;
  survived means the selected tests still passed. Separate timeouts, errors
  and untested mutants; do not count these as successful detections.
No minimum coverage, Pylint, Radon or mutation score is required. Explain what
results mean for your application. Passing tests and working evidence collection
remain CI requirements; metrics and AI opinions do not prove business value.

FOCUSED MUTATION CHECK — once before submission, outside CI
Choose ONE small function or module implementing an important business rule
(e.g. eligibility, price calculation or validation), with fast relevant tests.
Follow MUTATION_CHECK.txt for the Codespaces-tested 3.5.0 commands, exact
function filter and two-worker limit. Preserve shared dependencies; use its
optional isolated tool environment when needed. Do not run mutmut on every PR/main push, add it to
quality.yml, or make it a Render deployment gate. Complete the selected scope;
if it takes too long, narrow the scope rather than running the whole project.
Save the command, version/commit, selected scope, result counts and one example
in your existing submission or issue. Inspect a survivor if there is one; improve
a test or explain a justified decision. If all are killed, explain one detected
change and the test that catches it. Rerun the selected check if its code/tests
change. This can be your existing ONE quality decision, not an additional essay.
The automatic AI report still runs after successful CI on main; mutation output
is retained separately and is not automatically included in that report.

USE THE REPORT AS SUPPORTING EVIDENCE
For the release, use ONE AI-report finding OR focused mutation result to explain
a quality decision in an existing issue. Check code/tests/measurements, explain agreement or disagreement, and
fix, defer or dismiss with a reason. Link the retained report and evidence.
You do not owe an evaluation after every push or a separate AI project/report.
A green pipeline or AI opinion does not establish business value: demonstrate
working behavior and record specific stakeholder feedback and your response.

BEFORE SUBMITTING
Make sure your completed project passes its automated checks and works on
Render. Tag that tested version sprint-3. Do not change the tag after submitting.

SUBMIT ONCE PER TEAM
- Links to your repository, sprint-3 tag and deployed application.
- A short summary of what you delivered, why it matters to the stakeholder,
  and any known limitations.
- Links to stakeholder feedback and each member's code/test contributions.
- The passing workflow run and saved AI report, with a brief explanation of
  one quality decision and the focused mutation-check evidence.
- A brief note confirming you tested the deployed application and that its
  database data survives a redeployment.
Put these in one Canvas submission. You may link an existing GitHub issue if
that is easier; a separate release-evidence issue is optional. Check grader
access and save the report before artifacts expire. No extra essay is needed.

WHERE TO LOOK WHEN NEEDED
SETUP_REFERENCE.txt: exact local commands, integration details, gateway limits
and troubleshooting. SAMPLE_REPORT.md and sample-evidence: synthetic examples.
Deployment guide (Render-only build/Gunicorn; preserve local dependencies):
https://docs.google.com/document/d/1kFwsMl1WJQqpgnCJZnlUDi_aafPUirSBpkRgkVCsAoI/edit
