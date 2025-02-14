# Verwenden Sie ein offizielles Python-Image als Basis
FROM python:3.11-slim

# Setzen Sie das Arbeitsverzeichnis im Container
WORKDIR /app

# Kopieren Sie die Anforderungen in das Arbeitsverzeichnis
COPY requirements.txt requirements.txt

# Installieren Sie die Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

# Kopieren Sie den Rest des Anwendungscodes in das Arbeitsverzeichnis
COPY . .

# Setzen Sie die Umgebungsvariablen
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Exponieren Sie den Port, auf dem die Anwendung läuft
EXPOSE 5001

# Starten Sie die Anwendung
CMD ["flask", "run", "--host=0.0.0.0", "--port=5001"]