import streamlit as st
import pandas as pd
from datetime import datetime
from helpers import get_meeting_dates, generate_roster, get_sg_public_holidays

st.set_page_config(page_title="Bible Study Roster Generator", layout="centered")
st.title("\ud83d\udcd6 Bible Study Roster Generator")

# Session state for regenerating with relaxed rules and manual entries
if "regenerate_mode" not in st.session_state:
    st.session_state.regenerate_mode = False
if "manual_fixes" not in st.session_state:
    st.session_state.manual_fixes = {}

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

    # Remove duplicates and warn
    duplicates = [name for name in members if members.count(name) > 1]
    members = list(dict.fromkeys(members))
    if duplicates:
        st.warning(f"Duplicate names removed: {', '.join(set(duplicates))}")

    st.markdown("### Optional: Mark member unavailability (by month number)")
    unavailable = {}
    for member in members:
        months = st.multiselect(f"Unavailable months for {member}:", list(range(1, 13)), key=f"unavail_{member}")
        unavailable[member] = months

    include_holidays = st.checkbox("Avoid Singapore public holidays?", value=True)

    submitted = st.form_submit_button("Generate Roster")

if submitted or st.session_state.regenerate_mode:
    if not members or not weeks:
        st.error("Please input both members and valid week selections.")
    else:
        dates = get_meeting_dates(year, weekday_index, [w - 1 for w in weeks])
        if include_holidays:
            sg_holidays = get_sg_public_holidays(year)
            dates = [d for d in dates if d not in sg_holidays]

        avoid_back_to_back = not st.session_state.regenerate_mode
        roster, summary = generate_roster(dates, members, unavailable, avoid_back_to_back)

        # Apply manual fixes
        for fix_date, fixed_name in st.session_state.manual_fixes.items():
            fix_date = datetime.strptime(fix_date, "%Y-%m-%d").date()
            idx = roster[roster["Date"] == fix_date].index
            if not idx.empty:
                roster.at[idx[0], "Facilitator"] = fixed_name

        st.success("Roster Generated!")

        st.markdown("### Meeting Roster")
        month_map = {}
        for _, row in roster.iterrows():
            key = row["Date"].strftime("%b %Y")
            if key not in month_map:
                month_map[key] = []
            month_map[key].append((row["Date"].strftime("%d %a"), row["Facilitator"], row["Date"]))

        months_sorted = sorted(month_map.keys(), key=lambda x: datetime.strptime(x, "%b %Y"))
        num_cols = 2 if len(months_sorted) > 8 else 3
        rows = [months_sorted[i:i+num_cols] for i in range(0, len(months_sorted), num_cols)]
        tba_dates = []

        for row in rows:
            cols = st.columns(len(row))
            for idx, month in enumerate(row):
                with cols[idx]:
                    st.markdown(f"**{month}**")
                    for date_str, facilitator, date_obj in month_map[month]:
                        if facilitator == "TBA":
                            tba_dates.append(date_obj)
                        st.markdown(f"{date_str}: {facilitator}")

        if tba_dates:
            st.warning("Some dates could not be assigned due to constraints:")
            for d in tba_dates:
                st.markdown(f"- {d.strftime('%a, %d %b %Y')}: No eligible members (due to availability or constraints)")

            st.markdown("---")
            st.markdown("### Resolve TBA Slots")

            if st.button("Regenerate without back-to-back restriction"):
                st.session_state.regenerate_mode = True
                st.rerun()

            for tba_date in tba_dates:
                st.markdown(f"**Manually assign for {tba_date.strftime('%a, %d %b %Y')}:**")
                chosen = st.selectbox(
                    f"Assign someone:", members, key=f"manual_{tba_date}"
                )
                if st.button(f"Confirm assignment for {tba_date}"):
                    st.session_state.manual_fixes[str(tba_date)] = chosen
                    st.session_state.regenerate_mode = False
                    st.rerun()

        st.markdown("### Assignment Summary")
        cols = st.columns(4)
        for i, (member, count) in enumerate(summary.values):
            cols[i % 4].metric(label=member, value=int(count))

        def convert_df(df):
            return df.to_csv(index=False).encode('utf-8')

        st.download_button("\ud83d\udcc5 Download Roster (CSV)", convert_df(roster), "roster.csv", "text/csv")
        st.download_button("\ud83d\udcc5 Download Summary (CSV)", convert_df(summary), "summary.csv", "text/csv")
