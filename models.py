from app import db

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    link = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f"<Project {self.title}>"
