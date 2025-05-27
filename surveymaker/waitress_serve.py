from waitress import serve
from surveymaker.wsgi import application
import os


serve(
    application,
    host='0.0.0.0',  # Listen on all available interfaces
    port=8000,       # Port to listen on
    threads=4        # Number of worker threads
)

print("Waitress server started on http://0.0.0.0:8000")