# run.py

from project import create_app, db
from flask_migrate import Migrate

# Create the Flask app instance
app = create_app()

# Initialize Flask-Migrate
# This line is CRITICAL for the 'flask db' command to work
migrate = Migrate(app, db)

if __name__ == '__main__':
    app.run(debug=True)
