# database_QSL_project

# Database Flask 

This project is a Flask web application connected to a PostgreSQL database using SQLAlchemy.  
It demonstrates database integration, CRUD logic, HTML templating, and deployment on Render.

---

## Running the Application Locally

### 1. Install dependencies
Run the following command inside the project folder:

pip install -r requirements.txt

### 2. Create a `.env` file
The application uses environment variables for configuration.  
Create a `.env` file in the project root and include:

DATABASE_URL=your_postgresql_connection_string  
SECRET_KEY=your_secret_key

Do not commit your `.env` file to GitHub.

### 3. Start the Flask application

python -m flask run

The application will be available at:
http://127.0.0.1:5000

---

## Database Setup

The SQLAlchemy models are defined in `models.py`.  
Database tables are created automatically when the application starts.

---

## Deployment on Render

### 1. Push the project to GitHub  
Ensure `.env` is ignored using `.gitignore`.

### 2. Create a new Web Service on Render  
Select the GitHub repository and choose the Python environment.

### 3. Add environment variables on Render  
In the Render dashboard, add:

DATABASE_URL = your PostgreSQL connection string  
SECRET_KEY = your secret key  

### 4. Build and start commands

Build command:
pip install -r requirements.txt

Start command:
gunicorn app:app

### 5. Deploy the service  
Render will install dependencies, start the application, and provide a public URL.

---

## Project Structure

DATABASE_QSL_PROJECT/  
│  
├── app.py  
├── config.py  
├── models.py  
├── requirements.txt  
├── runtime.txt  
├── .gitignore  
├── README.md  
├── templates/  
├── static/  
└── .env (not included in GitHub)

---

## Features

- Flask routing  
- SQLAlchemy ORM  
- PostgreSQL integration  
- CRUD operations  
- HTML templates  
- CSS and JavaScript support  
- Deployment on Render

---

## Notes

- The `.env` file must remain private.  
- Render uses environment variables instead of your local `.env`.  
- The application runs both locally and on Render.
