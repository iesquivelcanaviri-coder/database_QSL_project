from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        from models import Project
        db.create_all()

    @app.route("/")
    def home():
        return render_template("home.html")

    @app.route("/projects")
    def projects():
        all_projects = Project.query.all()
        return render_template("projects.html", projects=all_projects)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
