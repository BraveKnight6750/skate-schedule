import requests
import re
import json
from datetime import datetime
from ics import Calendar, Event as ICSEvent
import os
import pytz

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

URLS = [
    "https://starcenter.finnlyconnect.com/registration/activityitem/21100",
    "https://starcenter.finnlyconnect.com/registration/activityitem/20619",
]

central = pytz.timezone("America/Chicago")

class Event():

    def __init__(self,data:dict):
        self.event_id       = data["ActivityId"]
        self.facility_name  = data["DisplayFacility"]
        self.start_time = central.localize(datetime.fromisoformat(data["Start"]))
        self.end_time   = central.localize(datetime.fromisoformat(data["End"]))
        self.rinkName = self.facility_name[0:2]

facility_locations = {
    "PL - World Rink": "4020 W Plano Pkwy, Plano, TX 75093",
    "PL - US Rink":    "4020 W Plano Pkwy, Plano, TX 75093",
    "RC - Blue Rink":  "522 Centennial Blvd, Richardson, TX 75081",
    "RC - Red Rink":   "522 Centennial Blvd, Richardson, TX 75081",
    "MK - South Rink": "6993 Stars Ave, McKinney, TX 75070",
    "MK - North Rink": "6993 Stars Ave, McKinney, TX 75070"
}

allowed_facilities= {
    "PL - World Rink",
    "PL - US Rink",
    "RC - Blue Rink",
    "RC - Red Rink",
    "MK - South Rink",
    "MK - North Rink"
}

def parse_events_from_html(html: str) -> list:
    pattern = r'singleSessionSchedule.*?"Data":\s*(\[.*?\])\s*,\s*"Total":\s*\d+'
    match = re.search(pattern, html, re.DOTALL)
    if not match:
        return []
    schedule_list = json.loads(match.group(1))
    return [Event(e) for e in schedule_list if e["DisplayFacility"] in allowed_facilities]

def build_ics(events: list[Event], output_file="open_hockey.ics"):
    cal = Calendar()

    for event in events:
        e = ICSEvent()
        e.name     = f"{event.rinkName} - Open Hockey"
        e.begin    = event.start_time
        e.end      = event.end_time
        e.location = facility_locations.get(event.facility_name, "")
        e.description = f"Facility: {event.facility_name}"
        cal.events.add(e)

    with open(output_file, "w") as f:
        f.writelines(cal)

    print(f"Saved {len(events)} events to {output_file}")

#main
all_events = []
any_success = False

for url in URLS:
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch {url} (status {response.status_code}), skipping.")
        continue
    any_success = True
    events = parse_events_from_html(response.text)
    print(f"Found {len(events)} events from {url}")
    all_events.extend(events)

if not any_success:
    print("All URLs failed, exiting.")
    exit()

if not all_events:
    print("No matching events found for allowed facilities.")
    exit()

build_ics(all_events)

from github import Github, Auth

def upload_to_github(filepath="open_hockey.ics", 
                     token=os.environ.get("GH_TOKEN"),
                     repo_name="BraveKnight6750/skate-schedule"):

    g = Github(auth=Auth.Token(token))
    repo = g.get_repo(repo_name)

    with open(filepath, "r") as f:
        content = f.read()

    try:
        # Update existing file
        existing = repo.get_contents(filepath)
        repo.update_file(filepath, "Update schedule", content, existing.sha)
        print("Updated file on GitHub")
    except:
        # Create file if it doesn't exist yet
        repo.create_file(filepath, "Create schedule", content)
        print("Created file on GitHub")

upload_to_github()
