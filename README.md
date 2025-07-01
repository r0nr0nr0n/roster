# Bible Study Roster Generator

This is a flexible Streamlit app that generates a fair, non-repeating Bible study roster.

## 🔧 How to Set Up Locally

1. **Install Python:** https://www.python.org/downloads/
2. Open your terminal (Command Prompt, PowerShell, or Terminal)
3. Navigate to this folder and run:

```
pip install -r requirements.txt
streamlit run app.py
```

4. It will open in your browser at http://localhost:8501

## ☁️ Deploy Free on Streamlit Cloud

1. Create a GitHub account and upload these files to a repository.
2. Visit https://streamlit.io/cloud
3. Sign in with GitHub and select your repo and `app.py`
4. Done! You get a public URL for others to view.

## ✨ Features
- Input custom members, days, weeks, and unavailability
- Avoid back-to-back (and 1-meeting-apart) assignments
- Auto-skip Singapore public holidays
- Export roster and assignment summary as CSV