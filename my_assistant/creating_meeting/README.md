# Meeting Assistant

A smart CLI assistant that uses Groq AI to interpret natural language commands and manage your Google Calendar events.

## Features

- **Natural Language Parsing**: "Lunch with Sarah tomorrow at 1pm" becomes a structured calendar event.
- **Smart Contact Resolution**: Maps names to email addresses using a local `contacts.json` file.
- **Interactive & Command Line Mode**: Run it interactively or pass commands directly.
- **Google Calendar Integration**: Automatically checks for conflicts and adds events to your primary calendar.

## Prerequisites

- Python 3.8+
- A Google Cloud Project with the **Google Calendar API** enabled.
- An API Key from [Groq](https://groq.com/).

## Installation

1.  **Install Dependencies**:
    Navigate to the project root and install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Setup**:
    Create a `.env` file in the project root (or ensure it exists) and add your Groq API key:
    ```env
    GROQ_API_KEY=your_groq_api_key_here
    ```

## Authentication Setup

Before running the assistant, you need to authenticate with Google:

1.  **Download Credentials**:
    - Go to the [Google Cloud Console](https://console.cloud.google.com/).
    - Create an OAuth 2.0 Client ID (Desktop App).
    - Download the JSON file, rename it to `credentials.json`, and place it in this folder (`my_assistant/creating_meeting/`).

2.  **Generate Token**:
    Run the authentication script to authorize the app and generate a `token.json` file:
    ```bash
    python auth_check.py
    ```
    Follow the browser prompts to log in to your Google account. Once successful, a `token.json` file will be created.

## Configuration

### contacts.json
The app uses `contacts.json` to map names to email addresses. Ensure this file is present in the `creating_meeting` directory with the following structure:

```json
{
  "individuals": {
    "Sarah": "sarah@example.com",
    "Bob": "bob@example.com"
  },
  "groups": {
    "Team": ["alice@example.com", "charlie@example.com"]
  }
}
```

## Running the App

You can run the assistant in two ways:

### 1. Interactive Mode
Run the script without arguments to start an interactive session:
```bash
python assistant.py
```
Type your request when prompted.

### 2. Command Line Mode
Pass your request directly as a command-line argument:
```bash
python assistant.py "Schedule a team meeting for next Monday at 10am"
```

## Troubleshooting
- **Token Issues**: If you encounter authentication errors, delete `token.json` and run `python auth_check.py` again.
- **API Errors**: Ensure your Google Cloud Project has the Calendar API enabled and your quota is not exceeded.
