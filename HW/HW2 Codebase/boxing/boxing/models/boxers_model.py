from dataclasses import dataclass
import logging
import sqlite3
from typing import Any, List

from boxing.utils.sql_utils import get_db_connection
from boxing.utils.logger import configure_logger


logger = logging.getLogger(__name__)
configure_logger(logger)


@dataclass
class Boxer:
    """
    A class to manage a list of boxers.

    Attributes:
        id (int): Unique identifying number for the boxer
        name (str): Name of boxer
        weight (int): Weight of boxer in pounds
        height (int): Height of boxer in inches
        reach (float): Reach of boxer in inches
        age (int): Age of the boxer
        weight_class (str): Assigned weight class based on the boxer's weight
    """
    id: int
    name: str
    weight: int
    height: int
    reach: float
    age: int
    weight_class: str = None

def __post_init__(self):
    """assigns weight class based on the boxer's weight 
    
    """
    self.weight_class = get_weight_class(self.weight)  # Automatically assign weight class


    ##################################################
    # Boxer Management Functions
    ##################################################

def create_boxer(name: str, weight: int, height: int, reach: float, age: int) -> None:
    """
    Creates a new entry in the database.

    args:
        name (str): boxer's name
        weight (int): boxer's weight in pounds
        height (int): boxer's height in inches
        reach (float): boxer's reach in inches
        age (int): boxer's age
    raises:
        ValueError: If any input is invalid or if the boxer already exists
    """
    logger.info(f"Received request to create a boxer: {name}, {weight}, {height}, {reach}, {age}")

    if weight < 125:
        logger.error(f"Invalid weight: {weight}. Must be at least 125.")
        raise ValueError(f"Invalid weight: {weight}. Must be at least 125.")
    if height <= 0:
        logger.error(f"Invalid height: {height}. Must be greater than 0.")
        raise ValueError(f"Invalid height: {height}. Must be greater than 0.")
    if reach <= 0:
        logger.error(f"Invalid reach: {reach}. Must be greater than 0.")
        raise ValueError(f"Invalid reach: {reach}. Must be greater than 0.")
    if not (18 <= age <= 40):
        logger.error(f"Invalid age: {age}. Must be between 18 and 40.")
        raise ValueError(f"Invalid age: {age}. Must be between 18 and 40.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check if the boxer already exists (name must be unique)
            cursor.execute("SELECT 1 FROM boxers WHERE name = ?", (name,))
            if cursor.fetchone():
                logger.error(f"Boxer with name '{name}' already exists")
                raise ValueError(f"Boxer with name '{name}' already exists")

            cursor.execute("""
                INSERT INTO boxers (name, weight, height, reach, age)
                VALUES (?, ?, ?, ?, ?)
            """, (name, weight, height, reach, age))

            conn.commit()
            logger.info(f"Boxer '{name}' created successfully")

    except sqlite3.IntegrityError:
        logger.error(f"Boxer with name '{name}' already exists")
        raise ValueError(f"Boxer with name '{name}' already exists")

    except sqlite3.Error as e:
        logger.error(f"Database error while creating boxer: {e}")
        raise e


def delete_boxer(boxer_id: int) -> None:
    """
    Deletes a boxer from the database using ID

    args:
        boxer_id (int): ID of boxer to delete
    raises:
        ValueError: if boxer is not found
    """
    logger.info(f"Attempting to delete boxer with ID: {boxer_id}")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM boxers WHERE id = ?", (boxer_id,))
            if cursor.fetchone() is None:
                logger.warning(f"Boxer with ID {boxer_id} not found.")
                raise ValueError(f"Boxer with ID {boxer_id} not found.")

            cursor.execute("DELETE FROM boxers WHERE id = ?", (boxer_id,))
            conn.commit()

            logger.info(f"Boxer with ID {boxer_id} deleted successfully.")

    except sqlite3.Error as e:
        logger.error(f"Database error while deleting boxer: {e}")
        raise e

    ##################################################
    # Boxer Retrieval Functions
    ##################################################

def get_leaderboard(sort_by: str = "wins") -> List[dict[str, Any]]:
    """
    Displays the leaderboard and sorts by wins or win percentage

    args:
        sort_by (str, optional): sorting criteria ('wins' or 'win_pct') but defaults to 'wins'
    returns:
        List[dict[str, Any]]: list of dictionaries containing boxer stats
    """
    logger.info(f"Attempting to display leaderboard sorted by: {sort_by}")

    query = """
        SELECT id, name, weight, height, reach, age, fights, wins,
            (wins * 1.0 / fights) AS win_pct
        FROM boxers
        WHERE fights > 0
    """

    if sort_by == "win_pct":
        query += " ORDER BY win_pct DESC"
    elif sort_by == "wins":
        query += " ORDER BY wins DESC"
    else:
        logger.warning(f"Invalid sort_by parameter: {sort_by}")
        raise ValueError(f"Invalid sort_by parameter: {sort_by}")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

        leaderboard = []
        for row in rows:
            boxer = {
                'id': row[0],
                'name': row[1],
                'weight': row[2],
                'height': row[3],
                'reach': row[4],
                'age': row[5],
                'weight_class': get_weight_class(row[2]),  # Calculate weight class
                'fights': row[6],
                'wins': row[7],
                'win_pct': round(row[8] * 100, 1)  # Convert to percentage
            }
            leaderboard.append(boxer)

        logger.info(f"Leaderboard displayed successfully sorted by: {sort_by}")
        return leaderboard

    except sqlite3.Error as e:
        logger.error(f"Database error while displaying sorted leaderboard: {e}")
        raise e


def get_boxer_by_id(boxer_id: int) -> Boxer:
    """
    finds a boxer by ID

    args:
        boxer_id (int): ID of boxer
    returns:
        Boxer: the boxer object corresponding to the ID
    raises:
        ValueError: if boxer is not found
    """
    logger.info(f"Attempting to find boxer with ID: {boxer_id}")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, weight, height, reach, age
                FROM boxers WHERE id = ?
            """, (boxer_id,))

            row = cursor.fetchone()

            if row:
                boxer = Boxer(
                    id=row[0], name=row[1], weight=row[2], height=row[3],
                    reach=row[4], age=row[5]
                )
                logger.info(f"Boxer with ID {boxer_id} found successfully: {boxer.name}")
                return boxer
            else:
                logger.warning(f"Boxer with ID {boxer_id} not found.")
                raise ValueError(f"Boxer with ID {boxer_id} not found.")

    except sqlite3.Error as e:
        logger.error(f"Database error while getting boxer by ID: {e}")
        raise e


def get_boxer_by_name(boxer_name: str) -> Boxer:
    """
    finds a boxer by name

    args:
        boxer_name (str): name of oxer
    returns:
        Boxer: boxer object corresponding to the name
    raises:
        ValueError: If boxer is not found
    """
    logger.info(f"Attempting to find boxer by name: {boxer_name}")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, weight, height, reach, age
                FROM boxers WHERE name = ?
            """, (boxer_name,))

            row = cursor.fetchone()

            if row:
                boxer = Boxer(
                    id=row[0], name=row[1], weight=row[2], height=row[3],
                    reach=row[4], age=row[5]
                )
                logger.info(f"Boxer '{boxer_name}' found.")
                return boxer
            else:
                logger.warning(f"Boxer '{boxer_name}' not found.")
                raise ValueError(f"Boxer '{boxer_name}' not found.")

    except sqlite3.Error as e:
        logger.error(f"Database error while finding boxer by name: {e}")
        raise e


def get_weight_class(weight: int) -> str:
    """
    determines weight class of a boxer based on weight

    args:
        weight (int): weight of boxer in pounds
    returns:
        str: weight class of boxer
    raises:
        ValueError: if the weight is below the minimum threshold
    """
    logger.info(f"Attempting to determine weight class for weight: {weight}")

    if weight >= 203:
        weight_class = 'HEAVYWEIGHT'
    elif weight >= 166:
        weight_class = 'MIDDLEWEIGHT'
    elif weight >= 133:
        weight_class = 'LIGHTWEIGHT'
    elif weight >= 125:
        weight_class = 'FEATHERWEIGHT'
    else:
        logger.error(f"Invalid weight: {weight}. Weight must be at least 125.")
        raise ValueError(f"Invalid weight: {weight}. Weight must be at least 125.")

    logger.info(f"Weight class for weight {weight}: {weight_class}")
    return weight_class

    ##################################################
    # Update Functions
    ##################################################

def update_boxer_stats(boxer_id: int, result: str) -> None:
    """
    Updates the stats of a boxer after a fight

    args:
        boxer_id (int): ID of the boxer whose stats are about to be updated
        result (str): result of the fight so either 'win' or 'loss'
    raises:
        ValueError: if result is not 'win' or 'loss' or if boxer is not found in the database
        sqlite3.Error: if there is an error executing database operations
    """
    logger.info(f"Attempting to update stats for boxer ID {boxer_id} with result: {result}")

    if result not in {'win', 'loss'}:
        logger.error(f"Invalid result: {result}. Expected 'win' or 'loss'.")
        raise ValueError(f"Invalid result: {result}. Expected 'win' or 'loss'.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM boxers WHERE id = ?", (boxer_id,))
            if cursor.fetchone() is None:
                logger.warning(f"Boxer with ID {boxer_id} not found.")
                raise ValueError(f"Boxer with ID {boxer_id} not found.")

            if result == 'win':
                cursor.execute("UPDATE boxers SET fights = fights + 1, wins = wins + 1 WHERE id = ?", (boxer_id,))
            else:
                cursor.execute("UPDATE boxers SET fights = fights + 1 WHERE id = ?", (boxer_id,))

            conn.commit()

            logger.info(f"Boxer ID {boxer_id} stats updated successfully.")

    except sqlite3.Error as e:
        logger.error(f"Database error while updating boxer stats: {e}")
        raise e
