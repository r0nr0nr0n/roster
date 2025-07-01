import streamlit as st
import pandas as pd
from datetime import datetime
from helpers import get_meeting_dates, generate_roster, get_sg_public_holidays

st.set_page_config(page_title="Bible Study Roster Generator", layout="centered")
st.title("📖 Bible Study Roster Generator")

with st.form("setup_form"):
    year = st.number_input("Year", value=datetime.now().year, min_value=2024, max_value=2100)

    weekday = st.selectbox(
        "Meeting Day",
        options=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    )
    weekday_index = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(weekday)

    week_options = [1, 2, 3, 4, 5]
    weeks = st.multiselect("Weeks of the Month (e.g., 1st & 3rd)", week_options, default=[1, 3])

    members_raw = st.text_area("Enter Members (one per line)").strip()
    members = [m.strip() for m in members_raw.splitlines() if m.strip()]

    st.markdown("### Optional: Mark member unavailability (by month number)")
    unavailable = {}
    for member in members:
        months = st.multiselect(f"Unavailable months for {member}:", list(range(1, 13)), key=f"unavail_{member}")
        unavailable[member] = months

    include_holidays = st.checkbox("Avoid Singapore public holidays?", value=True)

    submitted = st.form_submit_button("Generate Roster")

if submitted:
    if not members or not weeks:
        st.error("Please input both members and valid week selections.")
    else:
        dates = get_meeting_dates(year, weekday_index, [w - 1 for w in weeks])
        if include_holidays:
            sg_holidays = get_sg_public_holidays(year)
            dates = [d for d in dates if d not in sg_holidays]

        roster, summary = generate_roster(dates, members, unavailable)

        st.success("Roster Generated!")

        st.markdown("### Meeting Roster")
        month_map = {}
        for _, row in roster.iterrows():
            key = row["Date"].strftime("%b %Y")
            if key not in month_map:
                month_map[key] = []
            month_map[key].append((row["Date"].strftime("%d %a"), row["Facilitator"]))

        months_sorted = sorted(month_map.keys(), key=lambda x: datetime.strptime(x, "%b %Y"))
        rows = [months_sorted[i:i+3] for i in range(0, len(months_sorted), 3)]
        for row in rows:
            cols = st.columns(len(row))
            for idx, month in enumerate(row):
                with cols[idx]:
                    st.markdown(f"**{month}**")
                    for date_str, facilitator in month_map[month]:
                        st.markdown(f"{date_str}: {facilitator}")

        st.markdown("### Assignment Summary")
        cols = st.columns(4)
        for i, (member, count) in enumerate(summary.values):
            cols[i % 4].metric(label=member, value=int(count))

        def convert_df(df):
            return df.to_csv(index=False).encode('utf-8')

        st.download_button("📅 Download Roster (CSV)", convert_df(roster), "roster.csv", "text/csv")
        st.download_button("📅 Download Summary (CSV)", convert_df(summary), "summary.csv", "text/csv")
