
import argparse
from pathlib import Path

import markdown
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Project configuration
BASE_DIR = Path(__file__).resolve().parent
TOKEN_FILE = BASE_DIR / "credentials" / "token.json"
SCOPES = ["https://www.googleapis.com/auth/blogger"]

# Use the verified Blogger account
BLOG_ID = "4572355022033183812"


def get_blogger_service():
    if not TOKEN_FILE.exists():
        raise FileNotFoundError(
            "OAuth token missing. Run blogger_auth.py first."
        )

    credentials = Credentials.from_authorized_user_file(
        str(TOKEN_FILE),
        SCOPES,
    )

    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        TOKEN_FILE.write_text(credentials.to_json())
        TOKEN_FILE.chmod(0o600)

    if not credentials.valid:
        raise RuntimeError(
            "OAuth credentials invalid. Run blogger_auth.py."
        )

    return build(
        "blogger",
        "v3",
        credentials=credentials,
    )


def prepare_article(file_path):
    article_path = Path(file_path).resolve()

    # Only accept articles inside our articles directory
    articles_dir = (BASE_DIR / "articles").resolve()

    if not article_path.is_relative_to(articles_dir):
        raise ValueError(
            "Article must be inside the articles directory."
        )

    if not article_path.is_file():
        raise FileNotFoundError(
            f"Article not found: {article_path}"
        )

    if article_path.suffix.lower() != ".md":
        raise ValueError("Only Markdown files are supported.")

    content = article_path.read_text(encoding="utf-8")

    if not content.strip():
        raise ValueError("Article is empty.")

    lines = content.splitlines()

    # Use the first Markdown H1 as the Blogger title
    title = next(
        (
            line[2:].strip()
            for line in lines
            if line.startswith("# ")
        ),
        article_path.stem.replace("-", " ").title(),
    )

    html = markdown.markdown(
        content,
        extensions=["fenced_code", "tables"],
    )

    return title, html


def create_draft(article_file):
    title, html = prepare_article(article_file)

    print(f"Article: {title}")
    print("Publishing mode: DRAFT ONLY")

    confirmation = input(
        "Create an unpublished Blogger draft? (yes/no): "
    )

    if confirmation.strip().lower() != "yes":
        print("Cancelled. No draft created.")
        return

    service = get_blogger_service()

    # Confirm the destination before creating a post
    blog = service.blogs().get(blogId=BLOG_ID).execute()

    print("Destination blog:", blog["name"])

    post = {
        "kind": "blogger#post",
        "title": title,
        "content": html,
    }

    result = (
        service.posts()
        .insert(
            blogId=BLOG_ID,
            body=post,
            isDraft=True,
        )
        .execute()
    )

    print("\nDraft created successfully!")
    print("Title:", result["title"])
    print("Post ID:", result["id"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create an unpublished Blogger draft."
    )

    parser.add_argument(
        "article",
        help="Path to a Markdown article.",
    )

    args = parser.parse_args()
    create_draft(args.article)