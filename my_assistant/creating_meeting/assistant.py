import datetime
import dateparser
import os
import json
from groq import Groq  
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

console = Console()
SCOPES = ['https://www.googleapis.com/auth/calendar'] 

def load_contacts():
    # Construct the path relative to the script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    contacts_path = os.path.join(script_dir, 'contacts.json')
    with open(contacts_path, 'r') as f:
        return json.load(f)

CONTACTS = load_contacts()

def get_calendar_service():
    if not os.path.exists('token.json'):
        console.print("[bold red]Error:[/bold red] token.json not found!")
        exit()
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    return build('calendar', 'v3', credentials=creds)

def list_upcoming_events(service, count=10): 
    now = datetime.datetime.now(datetime.UTC).isoformat()
    
    events_result = service.events().list(
        calendarId='primary', 
        timeMin=now,
        maxResults=count, 
        singleEvents=True,
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
    """Uses Groq's Llama model to parse text into JSON."""
    prompt = f"""
    Extract from: "{user_input}"
    Today is: {datetime.date.today()}
    Valid Guests: {list(CONTACTS.keys())}
    
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
    
    with console.status("[bold cyan]Groq is thinking (Lightning Fast)...") as status:
        data = ask_ai(user_input)
    
    attendees = [{"email": CONTACTS[name]} for name in data.get('guests', []) if name in CONTACTS]

    event_body = {
        'summary': data['summary'],
        'start': {'dateTime': data['time'], 'timeZone': 'UTC'},
        'end': {'dateTime': (dateparser.parse(data['time']) + datetime.timedelta(hours=1)).isoformat(), 'timeZone': 'UTC'},
        'attendees': attendees,
    }

    event = service.events().insert(calendarId='primary', body=event_body, sendUpdates='all').execute()
    console.print(Panel(f" [bold green]Event Added![/bold green]\n[white]{data['summary']} at {data['time']}[/white]", border_style="green"))

    event_link = event.get('htmlLink')
    console.print(Panel(
        f"[bold green]Event Created![/bold green]\n"
        f"[bold]Link:[/bold] [link={event_link}]{event_link}[/link]\n"
        f"[dim]Invited: {', '.join(data.get('guests', ['No one']))}[/dim]", 
        border_style="green"
    ))

if __name__ == "__main__":
    console.print(Panel.fit("⚡ [bold cyan]Groq-Powered AI Assistant[/bold cyan] ⚡", subtitle="v2.0"))
    user_text = console.input("[bold yellow]What's the plan?[/bold yellow]: ")
    add_intelligent_event(user_text)
    
    list_upcoming_events(get_calendar_service())