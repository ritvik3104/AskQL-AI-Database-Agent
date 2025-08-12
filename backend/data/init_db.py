# backend/data/init_db.py

import sqlite3
import os
from datetime import datetime

# Define the path for the database file
DB_FOLDER = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_FOLDER, "sample.db")

def create_database():
    """
    Creates and populates the SQLite database with a single table
    and multiple sample rows for demonstration.
    """
    # Remove the old database file if it exists to ensure a clean start
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("Removed old database.")

    try:
        # Connect to the SQLite database (this will create the file)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        print("Database created successfully.")

        # --- Create Table ---
        cursor.execute("""
        CREATE TABLE people (
            person_id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            date_of_birth TEXT NOT NULL,
            city TEXT NOT NULL,
            salary REAL
        );
        """)
        print("Table 'people' created.")

        # --- Insert Sample Data ---
        people_data = [
            (1, 'Alice', 'Johnson', 'alice.j@example.com', '1990-04-15', 'New York', 95000.00),
            (2, 'Bob', 'Smith', 'bob.s@example.com', '1985-08-23', 'London', 88000.00),
            (3, 'Charlie', 'Brown', 'charlie.b@example.com', '1992-01-10', 'San Francisco', 105000.00),
            (4, 'Diana', 'Prince', 'diana.p@example.com', '1988-03-22', 'Paris', 76000.00),
            (5, 'Ethan', 'Hunt', 'ethan.h@example.com', '1991-11-05', 'Berlin', 90000.00),
            (6, 'Fiona', 'Glenanne', 'fiona.g@example.com', '1994-02-17', 'Sydney', 97000.00),
            (7, 'George', 'Miller', 'george.m@example.com', '1987-06-29', 'Toronto', 82000.00),
            (8, 'Hannah', 'Wells', 'hannah.w@example.com', '1993-09-14', 'Dubai', 99000.00)
        ]
        cursor.executemany("INSERT INTO people VALUES (?, ?, ?, ?, ?, ?, ?)", people_data)
        print(f"Inserted {len(people_data)} records into 'people'.")

        # Commit the changes
        conn.commit()
        print("Data committed successfully.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    # This allows you to run the script directly to create the database
    create_database()
