import pandas as pd
from datetime import datetime, timedelta
import requests

def get_sg_public_holidays(year):
    url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/SG"
    res = requests.get(url)
    holidays = []
    if res.status_code == 200:
        for day in res.json():
            holidays.append(datetime.strptime(day["date"], "%Y-%m-%d").date())
    return holidays

def get_meeting_dates(year, weekday, weeks_of_month):
    dates = []
    for month in range(1, 13):
        first_day = datetime(year, month, 1)
        days_to_add = (weekday - first_day.weekday() + 7) % 7
        first_occurrence = first_day + timedelta(days=days_to_add)

        weekday_dates = []
        current = first_occurrence
        while current.month == month:
            weekday_dates.append(current.date())
            current += timedelta(days=7)

        for week_index in weeks_of_month:
            if week_index < len(weekday_dates):
                dates.append(weekday_dates[week_index])
    return sorted(dates)

import random

def generate_roster(dates, members, unavailable, avoid_back_to_back=True):
    assigned = []
    count = {m: 0 for m in members}
    prev_assigned = []

    for i, date in enumerate(dates):
        eligible = [m for m in members if date.month not in unavailable.get(m, [])]

        if avoid_back_to_back:
            if i > 0:
                eligible = [m for m in eligible if m != prev_assigned[-1]]
            if i > 1:
                eligible = [m for m in eligible if m != prev_assigned[-2]]

        if not eligible:
            chosen = "TBA"
        else:
            # Find minimum assignment count among eligible
            min_count = min(count[m] for m in eligible)
            min_assigned_members = [m for m in eligible if count[m] == min_count]
            chosen = random.choice(min_assigned_members)

        assigned.append((date, chosen))
        if chosen != "TBA":
            count[chosen] += 1
        prev_assigned.append(chosen)

    roster_df = pd.DataFrame(assigned, columns=["Date", "Facilitator"])
    summary_df = pd.DataFrame(list(count.items()), columns=["Member", "# Assignments"])
    return roster_df, summary_df