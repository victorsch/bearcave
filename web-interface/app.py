from flask import Flask, render_template
import json

app = Flask(__name__)

@app.route('/')
def show_entries():
    with open('../logs/logs-12-08-2022.json') as f:
        entries = json.load(f)
    return render_template('entries_template.html', entries=entries)