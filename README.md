# surveybuilder
SurveyMaker is a modern Django-based app for creating and managing customizable surveys. Users can build surveys from scratch or use templates, with support for multiple question types, live editing, and a sleek, responsive UI

 Features
 
Dynamic survey builder with live editing
Sample question templates
Multiple input types (text, choice, rating, date, etc.)
Two-column layout for easy editingn
Dark mode & theme toggle
Sound effects with toggle
Animated, responsive Bootstrap UI
Searchable, filterable dashboard

Tech Stack

Backend: Django
Frontend: Bootstrap 5
Database: SQLite 

setup

git clone https://github.com/lastbytee/surveybuilder.git
cd surveymaker
python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
