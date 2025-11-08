import mysql.connector

def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",       # change if not localhost
        user="root",            # your MySQL username
        password="",            # your MySQL password
        database="portfolio_db" # the database you created
    )
    return connection




