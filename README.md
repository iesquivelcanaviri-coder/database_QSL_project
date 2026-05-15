# database_QSL_project




How to run the app locally (without secrets)
Code
pip install -r requirements.txt
python -m flask run


Environment Variables  
This project uses environment variables for configuration.
Create a .env file in the project root with:

Code
DATABASE_URL=your_postgresql_connection_stringSECRET_KEY=your_secret_key