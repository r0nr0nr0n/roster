import streamlit as st
import pandas as pd
from datetime import datetime
from helpers import get_meeting_dates, generate_roster, get_sg_public_holidays

st.set_page_config(page_title="Bible Study Roster Generator", layout="centered")
st.title("Bible Study Roster Generator")

def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
    else:
        st.write("Please refresh the page manually.")

# Initialize session state
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
    year = st.number_input("Year", value=datetime.now().year, min_value=2024, max_value=2100)
    weekday = st.selectbox("Meeting Day", ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])
    weekday_index = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"].index(weekday)
    weeks = st.multiselect("Weeks of the Month", [1,2,3,4,5], default=[1,3])

    members = [m.strip() for m in st.text_area("Enter Members (one per line)").splitlines() if m.strip()]
    duplicates = [n for n in members if members.count(n) > 1]
    members = list(dict.fromkeys(members))
    if duplicates:
        st.warning(f"Duplicate names removed: {', '.join(set(duplicates))}")

    st.markdown("### Optional: Mark member unavailability")
    unavailable = {m: st.multiselect(f"{m} unavailable in:", list(range(1,13))) for m in members}

    include_holidays = st.checkbox("Avoid Singapore public holidays?", value=True)
    submitted = st.form_submit_button("Generate Roster")

if submitted:
    st.session_state.update({
        "saved_year": year,
        "saved_weekday_index": weekday_index,
        "saved_weeks": weeks,
        "saved_members": members,
        "saved_unavailable": unavailable,
        "saved_include_holidays": include_holidays,
        "inputs_saved": True,
        "regenerate_mode": False,
        "manual_fixes": {},
        "tba_dates": []
    })

def generate_and_display():
    if not st.session_state.inputs_saved:
        st.info("Enter details and click 'Generate Roster'.")
        return

    dates = get_meeting_dates(
        st.session_state.saved_year,
        st.session_state.saved_weekday_index,
        [w-1 for w in st.session_state.saved_weeks]
    )
    if st.session_state.saved_include_holidays:
        dates = [d for d in dates if d not in get_sg_public_holidays(st.session_state.saved_year)]

    roster, _ = generate_roster(
        dates,
        st.session_state.saved_members,
        st.session_state.saved_unavailable,
        not st.session_state.regenerate_mode
    )

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

    months = sorted(month_map.keys(), key=lambda x: datetime.strptime(x, "%b %Y"))
    rows = [months[i:i+3] for i in range(0, len(months), 3)]

    tbas = []
    for row in rows:
        cols = st.columns(len(row))
        for col, mon in zip(cols, row):
            with col:
                st.markdown(f"**{mon}**")
                for dstr, fac, dt in month_map[mon]:
                    if fac == "TBA":
                        tbas.append(dt)
                    st.markdown(f"{dstr}: {fac}")

    st.session_state.tba_dates = tbas.copy()
    if tbas:
        st.warning("Some slots could not be assigned:")
        pairs = [tbas[i:i+2] for i in range(0, len(tbas), 2)]
        st.markdown("---")
        st.markdown("### Resolve TBA Slots")

        if st.button("Regenerate without back-to-back restriction"):
            st.session_state.regenerate_mode = True
            safe_rerun()

        for pair in pairs:
            cols = st.columns(2)
            for idx, d in enumerate(pair):
                with cols[idx]:
                    st.markdown(f"**{d.strftime('%d %b, %a')}**")
                    sel = st.selectbox(
                        "", 
                        ["Select name..."] + st.session_state.saved_members,
                        key=f"manual_{d.isoformat()}",
                        label_visibility="collapsed"
                    )
                    if st.button("✔️ Confirm", key=f"confirm_{d.isoformat()}", use_container_width=True):
                        if sel != "Select name...":
                            st.session_state.manual_fixes[d.isoformat()] = sel
                            st.session_state.regenerate_mode = False
                            safe_rerun()

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

    csv = roster.to_csv(index=False).encode("utf-8")
    st.download_button("Download Roster", csv, "roster.csv", "text/csv")
    csv2 = summary.to_csv(index=False).encode("utf-8")
    st.download_button("Download Summary", csv2, "summary.csv", "text/csv")

generate_and_display()
