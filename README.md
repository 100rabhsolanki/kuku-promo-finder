# Promo Finder

A small Streamlit tool for shortlisting possible 20–60 second promo moments from timestamped episodic screenplay text. It is an editor-assist prototype: the ranking is keyword-based and heuristic, and every suggestion needs human review.

## Run locally

1. Install Python 3.10 or newer.
2. From the repository folder, create and activate a virtual environment if desired.
3. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Start the app:

   ```bash
   python -m streamlit run streamlit_app.py
   ```

5. Open the local address printed by Streamlit.

On Windows, `run_streamlit.bat` is also provided.

## Supported input

- One or more UTF-8 `.txt` screenplay files.
- A `.zip` archive containing UTF-8 `.txt` episode files.
- One pasted episode in the app.

The current parser expects timestamped blocks in the project’s structured format, for example:

```text
**CHARACTER (mood):**
Start: (00:12.00) | End: (00:15.00)
Dialogue goes here.
```

It recognizes `SCENE` sections and timestamped `CAMERA`, `ACTION`, dialogue, and sound-effect blocks. Ordinary scripts without timestamps, PDFs, and arbitrary screenplay layouts are not supported yet. The app reports parse warnings rather than claiming to understand unsupported formats.

Upload limits are 50 MB per upload, 10 MB per text script, 100 MB expanded ZIP content, and 100 scripts per run. ZIP members are read in memory and are not extracted to disk.

## What the results mean

The parser uses the screenplay’s timestamps. A proposed clip’s total duration is calculated from those timestamps, but the timestamps may not match final edited video. Candidate scores come from hand-written keyword and rubric rules; the app does not call an AI model and the scores are not validated against viewer or ad performance. It may miss subtle scenes or select lines that need story context. An editor should check the excerpt, timing, continuity, hook, and ending before using a candidate.

Use the CSV or JSON download to save a run’s output. The uploaded scripts are processed in temporary local files during the run; do not upload confidential material to a public deployment unless you control access to that deployment.

## Deploy to Streamlit Community Cloud

1. Push this repository to a GitHub repository you control.
2. Keep confidential screenplay inputs and outputs out of GitHub. This repository’s `.gitignore` excludes the assignment pack and generated submission outputs.
3. In Streamlit Community Cloud, create an app from the repository, choose the `main` branch, and set the app file to `streamlit_app.py`.
4. Deploy. Streamlit installs packages from the root `requirements.txt`.
5. Open the public link and try a harmless screenplay in the supported timestamp format.

The app does not need an API key. A public deployment is accessible to anyone with its URL; do not upload confidential screenplays there.
