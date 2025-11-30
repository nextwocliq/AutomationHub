from flask import Flask, request , jsonify , json 
from requests.auth import HTTPBasicAuth
from openai import OpenAI
import requests
import uuid
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv
load_dotenv()



GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME = os.getenv("REPO_NAME")

url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues"

SCOPES = ["https://www.googleapis.com/auth/calendar"]

email = os.getenv("EMAIL")
api_token = os.getenv("JIRA_API_TOKEN")
domain = os.getenv("JIRA_DOMAIN")

jiraurl = f"{domain}/rest/api/3/issue"

auth = HTTPBasicAuth(email, api_token)

store = {}

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


WebURL = os.getenv("CHANNEL_POST_URL")

@app.route("/", methods=["GET"])
def home():
    return """
    <h1>AutomationHub Python Server ✔️</h1>
    <p>Your Flask server is running correctly.</p>
    <p>Send POST requests to <b>/receive</b> from Deluge.</p>
    """


@app.route("/receive", methods=["POST"])
def receive():
    message = request.data.decode("utf-8")
    print("Message received:", message)
    message = "fix the login page issue within 1/1/26"

    prompt = """
    Analyze the given message and return ONLY JSON output (no explanation).
    {
      "category": "Developer Issue or Task creation or meeting creation or none",
      "subject": "",
      "timestamp": "",
      "deadline": "",
      "urgency": "",
      "mention_if_required": "",
      "posted_by": "",
      "explanation": ""
    }
    """

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": message}
        ]
    )

    reply = completion.choices[0].message.content.strip()
    print(reply)

    try:
        data = json.loads(reply)
    except:
        data = {"explanation": reply}

    store["parsed"] = data
    store["message"] = message

    
    #sendToCliq(data, message)

    return jsonify({"status": "success", "received_message": message}), 200


def sendToCliq(data, message):
    

    payload = {
        "text" : data 
    }


    headers = {
        "Content-Type": "application/json",
    }

    response = requests.post(WebURL, json=payload, headers=headers)

    print("\n--- Sent to Zoho Cliq ---")
    print("Payload:", payload)
    print("Status:", response.status_code)
    print("Response:", response.text)
    print("--------------------------\n")

@app.route("/create_jira", methods=["POST"])
def create_jira():
    data = store.get("parsed", {})
    msg = store.get("message", "No message received")

    head = {
    "Accept": "application/json",
    "Content-Type": "application/json"
    }

    payload = json.dumps({
    "fields": {
        "project": {
            "key": "KAN"
        },
        "summary": data.get("subject", ""),
        "description": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": data.get("explanation", "")
                        }
                    ]
                }
            ]
        },
        "issuetype": {
            "name": "Task"
        }
    }
    })
    response = requests.post(jiraurl, headers=head, auth=auth, data=payload)

    print(response.status_code)
    print(response.json().get("id"))

    if (response.status_code == 201):
        msg = data.get("subject","") + " is created Successfully and the id is " + response.json().get("id") + " 😄"
        sendToCliq(msg,200)
    else:
        msg = "Sorry I can't able to create the "+data.get("category","")+"😶"
        sendToCliq(msg,400)
    
    return jsonify({
        "status": response.status_code,
        "response": response.json()
    }), response.status_code


@app.route("/create_github", methods=["POST"])
def create_github():
    data = store.get("parsed", {})
    msg = store.get("message", "No message received")

    labels = []
    if data.get("category"):
        labels.append(data["category"])
    if data.get("urgency"):
        labels.append(data["urgency"])

    issue = {
        "title": data.get("subject", "No Subject Provided"),
        "body": data.get("explanation", "No description provided"),
        "assignees": ["nextwocliq"],
        "labels": labels
    }

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    response = requests.post(url, json=issue, headers=headers)
    print(response.status_code, response.text)

    if response.status_code in [200, 201]:
        sendToCliq(f"{issue['title']} created successfully", 200)
    else:
        sendToCliq("Failed to create GitHub issue", 400)

    return jsonify({"status": response.status_code, "response": response.json()}), response.status_code

def get_calendar_service():
    creds = None

    if os.path.exists("token.json"):
        with open("token.json", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.json", "wb") as token:
            pickle.dump(creds, token)

    return build("calendar", "v3", credentials=creds)

@app.route("/create_meet", methods=["GET", "POST"])
def create_meet():
    from datetime import datetime, timedelta

    service = get_calendar_service()
    data = store.get("parsed", {})

    start_time = data.get("timestamp")
    if not start_time or start_time == "":
        start_dt = datetime.utcnow()
    else:
        start_dt = datetime.fromisoformat(start_time)

    end_dt = start_dt + timedelta(hours=1) 

    event = {
        "summary": data.get("subject", "AutomationHub Meeting"),
        "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Kolkata"},
        "end":   {"dateTime": end_dt.isoformat(),   "timeZone": "Asia/Kolkata"},
        "conferenceData": {
            "createRequest": {
                "requestId": str(uuid.uuid4()),
                "conferenceSolutionKey": {"type": "hangoutsMeet"}
            }
        }
    }

    event_result = service.events().insert(
        calendarId="primary",
        body=event,
        conferenceDataVersion=1
    ).execute()

    meet_link = event_result.get("hangoutLink", "")

    print("Meet Link:", meet_link)

    service.events().delete(calendarId="primary", eventId=event_result["id"]).execute()

    if meet_link:
        sendToCliq("😁 The link is "+meet_link, 200)
    else:
        sendToCliq("Meet link not generated 😔", 400)

    return jsonify({"meet_link": meet_link}), 200



if __name__ == "__main__":
    print("Server running on http://127.0.0.1:3000")
    app.run(host="0.0.0.0", port=3000)
