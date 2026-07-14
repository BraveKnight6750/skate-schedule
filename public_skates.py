import requests
import json
import re
from ics import Calendar, Event as ICSEvent
from datetime import datetime


class Event:

    def __init__(self, data: dict):
        self.event_id = data["EventId"]
        self.facility_name = data["FacilityName"]
        self.account_name = data["AccountName"]
        self.start_time = datetime.fromisoformat(data["EventStartTime"])
        self.end_time = datetime.fromisoformat(data["EventEndTime"])
        self.event_type = data["EventTypeName"]


facility_locations = {
    "PL - World Rink": "4020 W Plano Pkwy, Plano, TX 75093",
    "PL - US Rink": "4020 W Plano Pkwy, Plano, TX 75093",
    "RC - Blue Rink": "522 Centennial Blvd, Richardson, TX 75081",
    "RC - Red Rink": "522 Centennial Blvd, Richardson, TX 75081",
    "MK - South Rink": "6993 Stars Ave, McKinney, TX 75070",
    "MK - North Rink": "6993 Stars Ave, McKinney, TX 75070",
}

allowed_facilities = {
    "PL - World Rink",
    "PL - US Rink",
    "RC - Blue Rink",
    "RC - Red Rink",
    "MK - South Rink",
    "MK - North Rink",
}


def build_ics(events: list[Event], output_file="public_skates.ics"):
    cal = Calendar()

    for event in events:
        e = ICSEvent()
        e.name = f"{event.account_name} - {event.event_type}"
        e.begin = event.start_time
        e.end = event.end_time
        e.location = facility_locations.get(event.facility_name, "")
        e.description = f"Facility: {event.facility_name}\nEvent ID: {event.event_id}"
        cal.events.add(e)

    with open(output_file, "w") as f:
        f.writelines(cal)


if __name__ == "__main__":
    url = "https://starcenter.finnlyconnect.com/schedule/833"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Site is down (status {response.status_code}), skipping this run.")
        exit()

    html = response.text
    match = re.search(r"_onlineScheduleList\s=\s(\[.*?\]);", html, re.DOTALL)

    if not match:
        print("no events found")
        exit()

    data = json.loads(match.group(1))

    events = [Event(e) for e in data if e["FacilityName"] in allowed_facilities]

    build_ics(events)
