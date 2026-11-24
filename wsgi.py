"""Entry point untuk `flask run` dan WSGI server (gunicorn / PythonAnywhere)."""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
