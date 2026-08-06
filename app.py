# ============================================================
# app.py
# Main entry point of the Flask application.
# Run this file to start the server:  python app.py
# ============================================================

from flask import Flask, render_template
from config import Config

# Import blueprints (route modules).
# As we build more features, we will register more blueprints here.
from routes.auth import auth_bp
from routes.student import student_bp
from routes.admin import admin_bp

def create_app():
    """
    Application factory function.
    Creates and configures the Flask app instance.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register blueprints -----------------------------------
    # Each blueprint handles a specific area of the app.
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)

    # Home page route -----------------------------------------
    @app.route("/")
    def home():
        """Landing page with links to student/admin login."""
        return render_template("index.html")

    return app


# Create the app instance
app = create_app()

if __name__ == "__main__":
    # debug=True enables auto-reload and detailed error pages.
    # Turn this off in production.
    app.run(debug=True)
