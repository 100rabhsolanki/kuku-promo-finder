@echo off
echo ========================================================
echo   Kuku Promo Finder - Launching Streamlit Web App
echo ========================================================
echo.

IF EXIST .venv\Scripts\streamlit.exe (
    echo Starting Streamlit from local virtual environment...
    .venv\Scripts\streamlit.exe run streamlit_app.py
) ELSE (
    echo Starting Streamlit with system python...
    py -m streamlit run streamlit_app.py
)
pause

