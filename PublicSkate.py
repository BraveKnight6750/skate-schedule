import requests
import re
import json
import subprocess
from datetime import datetime
from ics import Calendar, Event as ICSEvent
import os
import pytz

central = pytz.timezone("America/Chicago")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = requests.get("https://starcenter.finnlyconnect.com/schedule/833", headers=headers)

if response.status_code != 200:
    print(f"Site is down (status {response.status_code}), skipping this run.")
    exit()

print("Status code:", response.status_code)
html = response.text

class Event():

    def __init__(self,data:dict):
        self.event_id       = data["EventId"]
        self.facility_name  = data["FacilityName"]
        self.account_name   = data["AccountName"]
        self.start_time     = central.localize(datetime.fromisoformat(data["EventStartTime"]))
        self.end_time       = central.localize(datetime.fromisoformat(data["EventEndTime"]))
        self.event_type     = data["EventTypeName"]

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

def build_ics(events: list[Event], output_file="public_skates.ics"):
    cal = Calendar()

    for event in events:
        e = ICSEvent()
        e.name     = f"{event.account_name} - {event.event_type}"
        e.begin    = event.start_time
        e.end      = event.end_time
        e.location = facility_locations.get(event.facility_name, "")
        e.description = f"Facility: {event.facility_name}\nEvent ID: {event.event_id}"
        cal.events.add(e)

    with open(output_file, "w") as f:
        f.writelines(cal)

    print(f"Saved {len(events)} events to {output_file}")



#main
match = re.search(r'_onlineScheduleList\s*=\s*(\[.*?\]);', html, re.DOTALL) 

if not match:
       print("No events")
       exit() 
    
schedule_list = json.loads(match.group(1))

events = [Event(e) for e in schedule_list if e["FacilityName"] in allowed_facilities]
build_ics(events)


from github import Github, Auth

def upload_to_github(filepath="public_skates.ics", 
                    token = os.environ.get("GH_TOKEN"),
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
