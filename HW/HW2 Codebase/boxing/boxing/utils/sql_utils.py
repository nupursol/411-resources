from contextlib import contextmanager
import logging
import os
import sqlite3

from boxing.utils.logger import configure_logger


logger = logging.getLogger(__name__)
configure_logger(logger)


# load the db path from the environment with a default value
DB_PATH = os.getenv("DB_PATH", "/app/sql/boxing.db")


def check_database_connection():
    """
    checks if the database connection is successful by executing a query

    raises:
        Exception: If database connection is not OK or query fails
    """
    try:
        logger.info(f"Checking database connection to {DB_PATH}...")

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Execute a simple query to verify the connection is active
        cursor.execute("SELECT 1;")
        conn.close()

        logger.info("Database connection is healthy.")

    except sqlite3.Error as e:
        error_message = f"Database connection error: {e}"
        logger.error(error_message)
        raise Exception(error_message) from e

def check_table_exists(tablename: str):
    """
    checks if table exists by querying SQLite master table

    args:
        tablename (str): name of table to check
    raises:
        Exception: if table doesn't exist or theres an error with query
    """
    try:
        logger.info(f"Checking if table '{tablename}' exists in {DB_PATH}...")

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Use parameterized query to avoid SQL injection
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (tablename,))
        result = cursor.fetchone()

        conn.close()

        if result is None:
            error_message = f"Table '{tablename}' does not exist."
            logger.error(error_message)
            raise Exception(error_message)
        
        logger.info(f"Table '{tablename}' exists.")

    except sqlite3.Error as e:
        error_message = f"Table check error for '{tablename}': {e}"
        logger.error(error_message)
        raise Exception(error_message) from e

@contextmanager
def get_db_connection():
    """
    context manager for creating and managing an SQLite database connection

    yields:
        sqlite3.Connection: the SQLite connection object
    raises:
        sqlite3.Error: if theres an issue with the connection
    """
    conn = None
    try:
        logger.info(f"Opening database connection to {DB_PATH}...")
        conn = sqlite3.connect(DB_PATH)
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise e
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed.")
