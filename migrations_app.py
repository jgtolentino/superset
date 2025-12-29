"""
Flask application for database migrations
Minimal Flask app to enable Flask-Migrate commands
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize Flask app
app = Flask(__name__)

# Configure database URI from environment
# Prioritize SUPERSET__SQLALCHEMY_DATABASE_URI, fallback to SQLALCHEMY_DATABASE_URI
DATABASE_URI = os.getenv(
    'SUPERSET__SQLALCHEMY_DATABASE_URI',
    os.getenv(
        'SQLALCHEMY_DATABASE_URI',
        'postgresql+psycopg2://localhost/superset'
    )
)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Example model for demonstration
class ExampleModel(db.Model):
    """Example model for migration demonstration"""
    __tablename__ = 'example_migrations_table'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime, 
        server_default=db.func.now(),
        onupdate=db.func.now()
    )
    
    def __repr__(self):
        return f'<ExampleModel {self.name}>'


if __name__ == '__main__':
    print(f"Database URI: {DATABASE_URI[:50]}...")
    print("Use 'flask db' commands to manage migrations")
