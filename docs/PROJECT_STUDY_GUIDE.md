# Project Study & Interview Guide
## FASHSYST Technical Publishing Automation

**Project maturity:** verified development prototype. **Scope:** CLI-initiated creation of unpublished Blogger drafts, not automatic public publication.

## 1. What problem did we solve?

Technical articles about real engineering projects need repeatable preparation and review. Manually copying a formatted article into a blogging platform is repetitive and error-prone. We built a Python command-line application that reads a version-controlled Markdown article, converts it to HTML, and saves it as a **Blogger draft** after author confirmation.

**Business value:** the author spends more time documenting engineering decisions and less time on repeated formatting and transfer.

**Do not claim:** that this application is scheduled, deployed to production, fully tested, or capable of automatically publishing to DEV.to or LinkedIn. Those features are planned, not implemented.

## 2. Architecture — explain each stage

```text
Author writes article in articles/*.md
       |
       v
blogger_publish.py (CLI argument)
       |
       v
Validate: resolved path within articles/, .md extension, nonempty content
       |
       v
Get title: first "# " heading (or filename fallback)
       |
       v
Convert Markdown to HTML with Python markdown package
       |
       v
Explicit prompt: "Create ... draft?"  -- no --> stop
       |
      yes
       v
Load credentials/token.json; refresh expired access token if possible
       |
       v
Google Blogger API v3: blogs.get -> posts.insert(isDraft=True)
       |
       v
Unpublished Blogger draft -> human review in dashboard
```

**Key architectural separation:** `blogger_auth.py` obtains or refreshes authorization and displays accessible blogs. `blogger_publish.py` uses the saved authorization to submit a draft. A Markdown article is **content**, not Python code; the conversion stage bridges that difference.

## 3. Understand the implementation, not just the commands

### `blogger_auth.py`

1. `SCOPES = ["https://www.googleapis.com/auth/blogger"]` specifies the Blogger API permission the application requests.
2. `TOKEN_FILE` points to the local `credentials/token.json` file.
3. `Credentials.from_authorized_user_file(...)` loads saved credentials if that file exists.
4. When an access token is expired and a refresh token is available, `credentials.refresh(Request())` obtains a fresh access token.
5. If credentials are missing or invalid, `InstalledAppFlow.from_client_secrets_file(...)` starts Google's authorization flow using a local callback server (`port=0` asks the operating system to select a free port).
6. `TOKEN_FILE.write_text(credentials.to_json())` persists credentials locally; `chmod(0o600)` limits file permissions on the Unix filesystem.
7. `build("blogger", "v3", credentials=...)` constructs the Blogger client; `blogs().listByUser(userId="self").execute()` checks accessible blogs.

**Mental model:** OAuth 2.0 authorizes the application to act within the permissions granted by the user. The user does not need to embed a Google account password in the script.

### `blogger_publish.py`

1. `argparse` reads a positional Markdown article filename from the terminal.
2. `Path(file_path).resolve()` normalizes the input path, and `is_relative_to(articles_dir)` rejects paths outside the intended article directory.
3. The code checks `is_file()`, `.md` suffix, and nonempty content.
4. The first line starting with `# ` is used as the Blogger post title; if none exists, it derives a title from the filename.
5. `markdown.markdown(content, extensions=["fenced_code", "tables"])` converts headings, emphasis, lists, fenced code blocks, and tables into HTML.
6. The script asks the author to type `yes` before making the API call.
7. `get_blogger_service()` reads the existing OAuth token, refreshes it when possible, and creates the API client.
8. `blogs().get(blogId=BLOG_ID)` checks the configured destination blog.
9. `posts().insert(blogId=BLOG_ID, body=post, isDraft=True).execute()` creates an **unpublished draft**.
10. The resulting title and post ID are printed for verification.

**Important limitation:** each confirmed execution creates **a new** draft. It does not update an existing draft or detect duplicates.

## 4. Why use these technologies?

| Decision | Rationale | Alternative / trade-off |
| --- | --- | --- |
| Markdown files | Easy to read, diff, and version in Git | Rich text requires manual or specialized conversion |
| Python CLI | Quick integration with Google libraries and filesystem | A web service could offer remote/scheduled operation but needs hosting and access control |
| Google OAuth 2.0 | Delegated API permission without hardcoded account passwords | Service-account-style integration is not equivalent for this end-user Blogger workflow |
| Blogger API | Programmatic draft creation | Browser automation would be more fragile |
| Draft-only submission | Human review before public publication | Adds a manual approval step |
| GitHub | Version history and proof of implementation | Secrets and generated files must be excluded from commits |

## 5. Git and security lessons from this project

- `.gitignore` excludes `credentials/`, `token.json`, `.venv/` and local environment files from **new-file tracking**.
- `git check-ignore credentials/token.json` confirmed an ignore rule for the token.
- `git diff --cached --name-only` displayed the precise files staged for commit.
- `git diff --cached --check` checked for whitespace errors, **not** exposed secrets.
- `git remote -v` verified the configured GitHub remote; `git push -u origin main` uploaded the first commit and configured upstream tracking.
- A file committed **before** being ignored can remain in Git history; adding it to `.gitignore` does not erase that history.
- The hardcoded `BLOG_ID` identifies a destination blog; it is not an OAuth access token. It should eventually become configurable rather than remain in code.
- A public repository should never contain OAuth access tokens, refresh tokens, private keys, or the local OAuth client JSON.

**Threat-model question:** What if an untrusted user supplies article content? The current program trusts author-written Markdown, and the Markdown converter may preserve raw HTML. Future multi-user operation would require careful validation and content sanitization.

## 6. What did we verify?

**Observed and documented:**
- Google OAuth authorization succeeded and the Blogger API listed the blog.
- Python created an initial unpublished API test draft.
- The Markdown-based workflow created an article draft visible in the Blogger dashboard.
- The intended code and Markdown file were committed to GitHub.
- Two portfolio images were pushed: the draft dashboard and initial repository push.

**Not yet demonstrated:**
- Automated unit or integration test suite.
- CI pipeline for this specific repository.
- Retry and recovery behavior during network or quota failures.
- Duplicate prevention and update-in-place.
- Scheduling, production deployment, telemetry, or multi-platform distribution.

## 7. Troubleshooting scenarios to practice

**A. `FileNotFoundError` for article**

Check current working directory and supplied path using `pwd` and `ls -lh articles/`. The script resolves a relative path from the terminal's current directory, not automatically from its own folder.

**B. Missing OAuth token**

Run `python blogger_auth.py` in the project environment to authorize. Verify the `credentials/` directory is local and ignored, without sharing the token.

**C. Expired token, no valid refresh token**

Reauthorize with `blogger_auth.py`. The publishing script attempts a refresh when possible but does not initiate the interactive authorization flow itself.

**D. Blogger API returns unauthorized or forbidden**

Inspect the API error without logging tokens. Check which Google account granted access, requested scope, blog permissions, and configured `BLOG_ID`. Do not claim every 403 has the same root cause.

**E. Internet connection fails during API call**

The current implementation will surface an exception; it does not have built-in retries, idempotency, or recovery. Before retrying after an ambiguous failure, check Blogger Drafts to avoid creating a duplicate.

**F. A secret was committed accidentally**

Stop sharing the affected repository state, revoke/rotate compromised credentials, remove tracking, and assess whether Git history or forks contain the secret. `.gitignore` alone is insufficient.

## 8. Two-minute interview explanation (practice in your own words)

> I built a Python-based publishing automation prototype because I wanted technical project documentation to be repeatable instead of copied manually into Blogger. I write an article in Markdown and keep it in Git. The CLI validates that the file is in the expected article directory, extracts its heading, and converts the content into HTML. After explicit confirmation, the application uses a saved Google OAuth authorization to call the Blogger API and create an unpublished draft. I verified the draft through the Blogger dashboard, then documented the source and evidence in a separate GitHub repository. I excluded OAuth credentials from Git and kept publication under human review. The next engineering steps are automated tests, external configuration, structured error handling, and duplicate protection.

## 9. Interview questions — answer before reading the hints

1. **Why Markdown instead of plain text?** Because it represents document structure using lightweight syntax and is easily version-controlled.
2. **Why convert Markdown to HTML?** The Blogger post content is submitted as HTML.
3. **What does OAuth solve?** Delegated access without embedding an account password; token and scope management still matter.
4. **What is the difference between authentication and authorization here?** The user authenticates with Google, then grants the application permissions for Blogger operations.
5. **What does `isDraft=True` do?** Requests creation as an unpublished Blogger draft.
6. **What prevents traversal outside `articles/`?** Path resolution followed by an ancestor check against the resolved articles directory.
7. **What does `chmod(0o600)` mean?** Owner read/write only in standard Unix permission notation.
8. **Why does `.gitignore` not fully protect secrets?** It doesn't remove tracked or historical files and doesn't inspect source code for hardcoded tokens.
9. **What does `git diff --cached` inspect?** The staged/index changes planned for the next commit.
10. **What happens if the script is run twice?** It can create duplicate drafts.
11. **Where could the system fail?** File validation, parsing, expired or revoked credentials, permissions, API/network failures, and remote responses.
12. **How would you productionize it?** Add tests, CI, retry policy, structured logs, configuration, duplicate detection, secure secret management, and an explicit editorial approval workflow.

## 10. Practical competence exercises

Do these in a test branch, explain what you expect, and verify the result before claiming completion:

1. **Input validation:** Test a missing file, empty Markdown, a file outside `articles/`, and a non-`.md` file. Explain which error each case should produce.
2. **Title extraction:** Create an article with and without a `# ` heading. Predict the Blogger title. Test parsing without calling the API.
3. **Authorization reasoning:** Explain the difference between access tokens and refresh tokens; simulate the missing-token path without exposing credentials.
4. **Fault investigation:** Describe what you would check after an ambiguous network timeout to avoid creating a duplicate draft.
5. **Design review:** Propose a safer approach to configurable blog IDs, tests, and secret handling. Distinguish implemented features from future design.

### Completion criteria

**Built → Verified → Documented → Explained → Independently troubleshot.**

The repository currently meets the first three for its limited draft-creation scope. Complete the exercises and a verbal walkthrough before marking the study/interview stage complete.
