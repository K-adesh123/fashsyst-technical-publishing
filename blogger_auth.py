

from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Google Blogger permission
SCOPES = ["https://www.googleapis.com/auth/blogger"]

# Project paths
BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_DIR = BASE_DIR / "credentials"
TOKEN_FILE = CREDENTIALS_DIR / "token.json"


def get_credentials():
    # Reuse existing OAuth authorization
    credentials = None

    if TOKEN_FILE.exists():
        credentials = Credentials.from_authorized_user_file(
            str(TOKEN_FILE),
            SCOPES,
        )

    # Refresh expired access token
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    # Request authorization if necessary
    if not credentials or not credentials.valid:
        credentials_files = list(
            CREDENTIALS_DIR.glob("client_secret_*.json")
        )

        if not credentials_files:
            raise FileNotFoundError(
                "No OAuth client secret found in credentials/"
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(credentials_files[0]),
            SCOPES,
        )

        credentials = flow.run_local_server(
            host="localhost",
            port=0,
            open_browser=False,
        )

    # Save credentials securely
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(credentials.to_json())
    TOKEN_FILE.chmod(0o600)

    print("OAuth token saved successfully.")

    return credentials


def main():
    credentials = get_credentials()

    blogger = build(
        "blogger",
        "v3",
        credentials=credentials,
    )

    response = blogger.blogs().listByUser(
        userId="self"
    ).execute()

    blogs = response.get("items", [])

    if not blogs:
        print("Connection successful, but no blogs found.")
        return

    print("\nBlogger API connection successful!")

    for blog in blogs:
        print("\nBlog name:", blog["name"])
        print("Blog ID:", blog["id"])
        print("Blog URL:", blog["url"])


if __name__ == "__main__":
    main()