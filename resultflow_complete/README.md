# ResultFlow UI Redesign

## Windows quick setup
1. Extract this ZIP.
2. Open the `resultflow_complete` folder in VS Code.
3. Double-click `setup.bat` (or run it from a terminal). It creates a virtual environment, installs dependencies, and migrates the database. It also prompts to create an administrator account.
4. Run `run.bat` and open http://127.0.0.1:8000/.

If the setup script has already run, activate `venv` and run `python manage.py runserver`.

## Features retained
Django roles (admin, teacher, student), students, accounts, subject assignments, subjects, exams, marks, aggregate results, PDF/Excel exports. Existing SQLite database is included as the project base.
