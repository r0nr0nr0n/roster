import streamlit as st
import pandas as pd
from datetime import datetime
from helpers import get_meeting_dates, generate_roster, get_sg_public_holidays

st.set_page_config(page_title="Bible Study Roster Generator", layout="centered")
st.title("📖 Bible Study Roster Generator")

def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
    else:
        st.write("⚠️ Please refresh the page manually.")

# Initialize session state variables
initial_keys = {
    "inputs_saved": False,
    "saved_year": None,
    "saved_weekday_index": None,
    "saved_weeks": None,
    "saved_members": None,
    "saved_unavailable": None,
    "saved_include_holidays": None,
    "regenerate_mode": False,
    "manual_fixes": {},
    "tba_dates": [],
}
for key, val in initial_keys.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Input form
with st.form("setup_form"):
    year = st.number_input("Year", value=datetime.now().year, min_value=2024, max_value=2100, key="input_year")
    weekday = st.selectbox("Meeting Day", ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"], key="input_weekday")
    weekday_index = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"].index(weekday)
    weeks = st.multiselect("Weeks of the Month", [1,2,3,4,5], default=[1,3], key="input_weeks")

    members_raw = st.text_area("Enter Members (one per line)", key="input_members_raw").strip()
    members = [m.strip() for m in members_raw.splitlines() if m.strip()]
    duplicates = [n for n in members if members.count(n) > 1]
    members = list(dict.fromkeys(members))
    if duplicates:
        st.warning(f"Duplicate names removed: {', '.join(set(duplicates))}")

    st.markdown("### Optional: Mark member unavailability (by month)")
    unavailable = {}
    for m in members:
        months = st.multiselect(f"{m} unavailable in:", list(range(1,13)), key=f"unav_{m}")
        unavailable[m] = months

    include_holidays = st.checkbox("Avoid Singapore public holidays?", value=True, key="input_include_holidays")
    submitted = st.form_submit_button("Generate Roster")

# Save inputs on submit
if submitted:
    st.session_state.saved_year = year
    st.session_state.saved_weekday_index = weekday_index
    st.session_state.saved_weeks = weeks
    st.session_state.saved_members = members
    st.session_state.saved_unavailable = unavailable
    st.session_state.saved_include_holidays = include_holidays
    st.session_state.inputs_saved = True
    st.session_state.regenerate_mode = False
    st.session_state.manual_fixes = {}
    st.session_state.tba_dates = []

def generate_and_display():
    if not st.session_state.inputs_saved:
        st.info("Enter details and click 'Generate Roster'.")
        return

    dates = get_meeting_dates(
        st.session_state.saved_year,
        st.session_state.saved_weekday_index,
        [w - 1 for w in st.session_state.saved_weeks]
    )
    if st.session_state.saved_include_holidays:
        holidays = get_sg_public_holidays(st.session_state.saved_year)
        dates = [d for d in dates if d not in holidays]

    roster, _ = generate_roster(
        dates,
        st.session_state.saved_members,
        st.session_state.saved_unavailable,
        not st.session_state.regenerate_mode
    )

    # Apply manual fixes
    for fd_str, name in st.session_state.manual_fixes.items():
        fd = datetime.fromisoformat(fd_str).date()
        idx = roster[roster["Date"] == fd].index
        if not idx.empty:
            roster.at[idx[0], "Facilitator"] = name

    st.success("Roster Generated!")

    st.markdown("### Meeting Roster")
    month_map = {}
    for _, r in roster.iterrows():
        key = r["Date"].strftime("%b %Y")
        month_map.setdefault(key, []).append((r["Date"].strftime("%d %a"), r["Facilitator"], r["Date"]))

    months_sorted = sorted(month_map.keys(), key=lambda x: datetime.strptime(x, "%b %Y"))
    num_cols = 3
    rows = [months_sorted[i:i+num_cols] for i in range(0, len(months_sorted), num_cols)]
    tbas = []

    for row in rows:
        cols = st.columns(len(row))
        for ix, mon in enumerate(row):
            with cols[ix]:
                st.markdown(f"**{mon}**")
                for dstr, fac, dt in month_map[mon]:
                    if fac == "TBA":
                        tbas.append(dt)
                    st.markdown(f"{dstr}: {fac}")

    st.session_state.tba_dates = [d for d in tbas]
    if tbas:
        st.warning("⚠️ Some slots could not be assigned:")
        for d in tbas:
            st.markdown(f"- {d.strftime('%a, %d %b %Y')}")

        st.markdown("---")
        st.markdown("### Resolve TBA Slots")

        if st.button("Regenerate without back-to-back restriction"):
            st.session_state.regenerate_mode = True
            safe_rerun()

        for d in tbas:
            # Layout: date | dropdown | confirm button
            col_date, col_sel, col_btn = st.columns([1, 1, 0.5])
            with col_date:
                display_date = d.strftime("%d %a")
                # Inline highlighting if today
                if d == datetime.today().date():
                    display_date = f":red[{display_date}]"
                st.markdown(f"**{display_date}**")
            with col_sel:
                choices = ["Select name..."] + st.session_state.saved_members
                sel = st.selectbox("", choices, key=f"manual_{d}")
            with col_btn:
                if st.button("✔️", key=f"confirm_{d}", help="Confirm assignment"):
                    if sel and sel != "Select name...":
                        st.session_state.manual_fixes[d.isoformat()] = sel
                        st.session_state.regenerate_mode = False
                        safe_rerun()

    # Recalculate summary after manual fixes
    summary = (
        roster["Facilitator"]
        .value_counts()
        .reindex(st.session_state.saved_members, fill_value=0)
        .reset_index()
    )
    summary.columns = ["Member", "# Assignments"]

    st.markdown("### Assignment Summary")
    cols = st.columns(4)
    for i, (m, c) in enumerate(summary.values):
        cols[i % 4].metric(label=m, value=int(c))

    def to_csv(df):
        return df.to_csv(index=False).encode("utf-8")
    st.download_button("📅 Download Roster", to_csv(roster), "roster.csv", "text/csv")
    st.download_button("📅 Download Summary", to_csv(summary), "summary.csv", "text/csv")

generate_and_display()
