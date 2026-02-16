import sys
import datetime
import dateparser
import os
import json
from pathlib import Path 
from groq import Groq  
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from dotenv import load_dotenv
from rich.prompt import Confirm 

load_dotenv()


SCRIPT_DIR = Path(__file__).parent.absolute()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

console = Console()
SCOPES = ['https://www.googleapis.com/auth/calendar'] 

def load_contacts():
    contacts_path = SCRIPT_DIR / 'contacts.json'
    with open(contacts_path, 'r') as f:
        return json.load(f)

CONTACTS = load_contacts()

def get_calendar_service():
    token_path = SCRIPT_DIR / 'token.json'
    if not token_path.exists():
        console.print(f"[bold red]Error:[/bold red] token.json not found at {token_path}!")
        exit()
    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    return build('calendar', 'v3', credentials=creds)

def list_upcoming_events(service, count=10): 
    now = datetime.datetime.now(datetime.UTC).isoformat()
    events_result = service.events().list(
        calendarId='primary', timeMin=now,
        maxResults=count, singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])

    if not events:
        console.print("[yellow]No upcoming events found.[/yellow]")
        return

    table = Table(title="Your Upcoming Schedule", title_style="bold magenta", border_style="blue")
    table.add_column("Date", style="green") 
    table.add_column("Time", style="cyan")
    table.add_column("Event Description", style="white")

    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        if "T" in start:
            date_part = start.split("T")[0][5:]
            time_part = start.split("T")[1][:5]
        else:
            date_part = start[5:]
            time_part = "All Day"
        table.add_row(date_part, time_part, event['summary'])
    console.print(table)

def ask_ai(user_input):
    valid_names = list(CONTACTS["individuals"].keys()) + list(CONTACTS["groups"].keys())
    
    prompt = f"""
    Extract from: "{user_input}"
    Today is: {datetime.date.today()}
    Valid Guests/Groups: {valid_names}
    Return ONLY a JSON object:
    {{"summary": "text", "time": "ISO format string", "guests": ["names"]}}
    """
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a calendar assistant. Return ONLY JSON."},
            {"role": "user", "content": prompt}
        ],
        model="llama-3.3-70b-versatile", 
        response_format={"type": "json_object"}
    )
    return json.loads(chat_completion.choices[0].message.content)

def add_intelligent_event(user_input):
    service = get_calendar_service()
    
    with console.status("[bold cyan]My PA is cookingggg...") as status:
        data = ask_ai(user_input)
    
    console.print(Panel(
        f"[bold cyan]Proposed Event:[/bold cyan]\n"
        f"Task: {data['summary']}\n"
        f"Time: {data['time']}\n"
        f"Guests: {', '.join(data.get('guests', ['None']))}",
        title="AI Interpretation"
    ))

    if not Confirm.ask("Does this look correct?"):
        console.print("[yellow]Skipping. No event added.[/yellow]")
        return

    final_emails = set()
    for name in data.get('guests', []):
        if name in CONTACTS.get("groups", {}):
            final_emails.update(CONTACTS["groups"][name])
        elif name in CONTACTS.get("individuals", {}):
            final_emails.add(CONTACTS["individuals"][name])

    attendees = [{"email": email} for email in final_emails]

    start_dt = dateparser.parse(data['time'])
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=datetime.timezone.utc)
    end_dt = start_dt + datetime.timedelta(hours=1)

    event_body = {
        'summary': data['summary'],
        'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'UTC'},
        'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'UTC'},
        'attendees': attendees,
    }

    event = service.events().insert(calendarId='primary', body=event_body, sendUpdates='all').execute()
    
    event_link = event.get('htmlLink')
    console.print(Panel(
        f"[bold green]✔ Success! Event Created![/bold green]\n"
        f"[bold]Link:[/bold] {event_link}\n"
        f"[dim]Invited: {', '.join(data.get('guests', ['No one']))}[/dim]", 
        border_style="green"
    ))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_text = " ".join(sys.argv[1:])
    else:
        console.print(Panel.fit("[bold cyan]Emmatt's AI Assistant[/bold cyan]", subtitle="v1.0"))
        user_text = console.input("[bold yellow]What's the plan?[/bold yellow]: ")
    
    add_intelligent_event(user_text)
    list_upcoming_events(get_calendar_service())