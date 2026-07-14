import requests
import re
import json
from datetime import datetime
from ics import Calendar, Event as ICSEvent
import os
from zoneinfo import ZoneInfo

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

URLS = [
    # mckinney
    "https://starcenter.finnlyconnect.com/registration/activityitemv2/32592",
    # richardson
    "https://starcenter.finnlyconnect.com/registration/activityitemv2/32129",
    # plano
    "https://starcenter.finnlyconnect.com/registration/activityitemv2/32330",
]

LOCAL_TZ = ZoneInfo("America/Chicago")


class Event:

    def __init__(self, data: dict):
        self.event_id = data["ActivityId"]
        self.facility_name = data["DisplayFacility"]
        self.start_time = datetime.fromisoformat(data["Start"]).replace(tzinfo=LOCAL_TZ)
        self.end_time = datetime.fromisoformat(data["End"]).replace(tzinfo=LOCAL_TZ)
        self.abbrev = abbreviations.get(
            self.facility_name, self.facility_name[0:2].upper()
        )


facility_locations = {
    "PL - World Rink": "4020 W Plano Pkwy, Plano, TX 75093",
    "PL - US Rink": "4020 W Plano Pkwy, Plano, TX 75093",
    "Plano": "4020 W Plano Pkwy, Plano, TX 75093",
    "RC - Blue Rink": "522 Centennial Blvd, Richardson, TX 75081",
    "RC - Red Rink": "522 Centennial Blvd, Richardson, TX 75081",
    "Richardson": "522 Centennial Blvd, Richardson, TX 75081",
    "MK - South Rink": "6993 Stars Ave, McKinney, TX 75070",
    "MK - North Rink": "6993 Stars Ave, McKinney, TX 75070",
    "McKinney": "6993 Stars Ave, McKinney, TX 75070",
}

allowed_facilities = {
    "Plano",
    "MK - South Rink",
    "MK - North Rink",
    "McKinney",
    "Richardson",
}

abbreviations = {"Richardson": "RC", "McKinney": "MK", "Plano": "PL"}


def build_ics(events: list[Event], output_file="open_hockey.ics"):
    cal = Calendar()

    for event in events:
        e = ICSEvent()
        e.name = f"{event.abbrev} - Open Hockey"
        e.begin = event.start_time
        e.end = event.end_time
        e.location = facility_locations.get(event.facility_name, "")
        e.description = f"Facility: {event.facility_name}\nEvent ID: {event.event_id}"
        cal.events.add(e)

    with open(output_file, "w") as f:
        f.writelines(cal)


if __name__ == "__main__":
    all_events = []
    for url in URLS:
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Site is down (status {response.status_code}), skipping site {url}")
            continue

        html = response.text

        match = re.search(r"registrationScheduleList:\s(\[.*?\])", html, re.DOTALL)

        if not match:
            print(f"no events found for {url}")
            continue

        data = json.loads(match.group(1))

        events = [Event(e) for e in data if e["DisplayFacility"] in allowed_facilities]
        all_events.extend(events)

    if not all_events:
        print(f"no events found")
        exit()
    build_ics(all_events)
