from contextlib import contextmanager
import re
import sqlite3

import pytest

from boxing.models.boxers_model import (
    Boxer,
    create_boxer,
    delete_boxer,
    get_leaderboard,
    get_boxer_by_id,
    get_boxer_by_name,
    get_weight_class,
    update_boxer_stats
)

######################################################
#
#    Fixtures
#
######################################################

def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

# Mocking the database connection for tests
@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_cursor.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch("boxing.models.boxers_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test


######################################################
#
#    Create and delete
#
######################################################

def test_create_boxer(mock_cursor):
    """Test creating a boxer.

    """
    create_boxer(name= "Boxer Name", weight= 150, height= 71, reach= 72.2, age= 21)

    expected_query = normalize_whitespace("""
        INSERT INTO boxers (name, weight, height, reach, age)
        VALUES (?, ?, ?, ?, ?)
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call (second element of call_args)
    actual_arguments = mock_cursor.execute.call_args[0][1]
    expected_arguments = ("Boxer Name", 150, 71, 72.2, 21)

    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_create_boxer_duplicate(mock_cursor):
    """Test creating a boxer with a duplicate name (should raise an error).

    """
     # Simulate that the database will raise an IntegrityError due to a duplicate entry
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: boxers.name")

    with pytest.raises(ValueError, match="Boxer with name 'Boxer Name' already exists"):
        create_boxer(name="Boxer Name", weight=155, height=72, reach=73.0, age=21)

def test_create_boxer_invalid_weight():
    """Test error when trying to create a boxer with an invalid weight (e.g., less than 125)
    
    """

    with pytest.raises(ValueError, match=r"Invalid weight: 100. Must be at least 125."):
        create_boxer(name="Boxer Name", weight=100, height=71, reach=72.2, age=21)

def test_create_boxer_invalid_height():
    """Test error when trying to create a boxer with an invalid height (e.g., less than 0)
    
    """

    with pytest.raises(ValueError, match=r"Invalid height: -10. Must be greater than 0."):
        create_boxer(name="Boxer Name", weight=150, height=-10, reach=72.2, age=21)

def test_create_boxer_invalid_reach():
    """Test error when trying to create a boxer with an invalid reach (e.g., less than 0)
    
    """

    with pytest.raises(ValueError, match=r"Invalid reach: -10. Must be greater than 0."):
        create_boxer(name="Boxer Name", weight=150, height=71, reach=-10, age=21)

def test_create_boxer_invalid_age():
    """Test error when trying to create a boxer with an invalid age (e.g., <18 or >40)

    """
    with pytest.raises(ValueError, match=r"Invalid age: 16. Must be between 18 and 40."):
        create_boxer(name = "Boxer Name", weight = 150, height = 71, reach = 72.2, age = 16)

    with pytest.raises(ValueError, match=r"Invalid age: 41. Must be between 18 and 40."):
        create_boxer(name = "Boxer Name", weight = 150, height = 71, reach = 72.2, age = 41)

def test_delete_boxer(mock_cursor):
    """Test deleting a boxer by boxer ID.

    """
    # Simulate the existence of a boxer w/ id=1
    # We can use any value other than None
    mock_cursor.fetchone.return_value = (True)

    delete_boxer(1)

    expected_select_sql = normalize_whitespace("SELECT id FROM boxers WHERE id = ?")
    expected_delete_sql = normalize_whitespace("DELETE FROM boxers WHERE id = ?")

    # Access both calls to `execute()` using `call_args_list`
    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_delete_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    assert actual_select_sql == expected_select_sql, "The SELECT query did not match the expected structure."
    assert actual_delete_sql == expected_delete_sql, "The UPDATE query did not match the expected structure."

    # Ensure the correct arguments were used in both SQL queries
    expected_select_args = (1,)
    expected_delete_args = (1,)

    actual_select_args = mock_cursor.execute.call_args_list[0][0][1]
    actual_delete_args = mock_cursor.execute.call_args_list[1][0][1]

    assert actual_select_args == expected_select_args, f"The SELECT query arguments did not match. Expected {expected_select_args}, got {actual_select_args}."
    assert actual_delete_args == expected_delete_args, f"The UPDATE query arguments did not match. Expected {expected_delete_args}, got {actual_delete_args}."

def test_delete_boxer_invalid_id(mock_cursor):
    """Test error when trying to delete a non-existent boxer.

    """
    # Simulate that no song exists with the given ID
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match="Boxer with ID 999 not found"):
        delete_boxer(999)


######################################################
#
#    Get leaderboard and boxer
#
######################################################


def test_get_leaderboard(mock_cursor):
    """Test getting leaderboard sorted by wins.
    
    """
    mock_cursor.fetchall.return_value = [
        (1, "Boxer A", 150, 71, 72.2, 21, 12, 9, 0.75),
        (2, "Boxer B", 180, 75, 77.5, 24, 25, 10, 0.4),
    ]

    leaderboard = get_leaderboard()

    expected = [
        {
            'id': 1, 'name': "Boxer A", 'weight': 150, 'height': 71,
            'reach': 72.2, 'age': 21, 'weight_class': 'LIGHTWEIGHT',
            'fights': 12, 'wins': 9, 'win_pct': 75.0
        },
        {
            'id': 2, 'name': "Boxer B", 'weight': 180, 'height': 75,
            'reach': 77.5, 'age': 24, 'weight_class': 'MIDDLEWEIGHT',
            'fights': 25, 'wins': 10, 'win_pct': 40.0
        }
    ]

    assert leaderboard == expected

def test_get_leaderboard_invalid_sort():
    """Test getting leaderboard with invalid sort_by parameter.
    
    """
    with pytest.raises(ValueError, match="Invalid sort_by parameter: invalid"):
        get_leaderboard(sort_by="invalid")

def test_get_boxer_by_id(mock_cursor):
    """Test getting a boxer by id.

    """
    mock_cursor.fetchone.return_value = (1, "Boxer Name", 150, 71, 72.2, 21, False)

    result = get_boxer_by_id(1)

    expected_result = Boxer(1, "Boxer Name", 150, 71, 72.2, 21)

    assert result == expected_result, f"Expected {expected_result}, got {result}"

    expected_query = normalize_whitespace("SELECT id, name, weight, height, reach, age FROM boxers WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    actual_arguments = mock_cursor.execute.call_args[0][1]
    expected_arguments = (1,)

    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_get_boxer_by_id_invalid_id(mock_cursor):
    """Test error when getting a non-existent boxer.

    """
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match="Boxer with ID 999 not found"):
        get_boxer_by_id(999)

def test_get_boxer_by_name(mock_cursor):
    """Test retrieving a boxer by name.
    
    """
    mock_cursor.fetchone.return_value = (1, "Boxer A", 150, 71, 72.2, 21)

    result = get_boxer_by_name("Boxer A")

    expected = Boxer(id=1, name="Boxer A", weight=150, height=71, reach=72.2, age=21)
    assert result == expected, f"Expected {expected}, got {result}"

    expected_query = normalize_whitespace("""
        SELECT id, name, weight, height, reach, age
        FROM boxers WHERE name = ?
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    actual_args = mock_cursor.execute.call_args[0][1]

    assert actual_query == expected_query
    assert actual_args == ("Boxer A",)

def test_get_boxer_by_invalid_name(mock_cursor):
    """Test retrieving a non-existent boxer by name.
    
    """
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match="Boxer 'Invalid' not found."):
        get_boxer_by_name("Invalid")


######################################################
#
#    Get weight class
#
######################################################


def test_get_weight_class():
    """Test that weights are correctly categorizes into weight classes.
    
    """
    assert get_weight_class(203) == "HEAVYWEIGHT"
    assert get_weight_class(166) == "MIDDLEWEIGHT"
    assert get_weight_class(133) == "LIGHTWEIGHT"
    assert get_weight_class(125) == "FEATHERWEIGHT"

def test_get_weight_class_invalid_weight():
    """Test get_weight_class error raising for weights below 125.
    
    """

    with pytest.raises(ValueError, match="Invalid weight: 120. Weight must be at least 125."):
        get_weight_class(120)


######################################################
#
#    Update Stats
#
######################################################


def test_update_boxer_stats_win(mock_cursor):
    """Test that updating stats works by incrementing both fights and wins by 1 after a win.
    
    """

    mock_cursor.fetchone.return_value = True
    update_boxer_stats(1, "win")

    update_query = normalize_whitespace("UPDATE boxers SET fights = fights + 1, wins = wins + 1 WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])
    actual_args = mock_cursor.execute.call_args_list[1][0][1]

    assert actual_query == update_query
    assert actual_args == (1,)

def test_update_boxer_stats_loss(mock_cursor):
    """Test that updating stats works by incrementing just the fights by 1 after a loss.
    
    """

    mock_cursor.fetchone.return_value = True
    update_boxer_stats(1, "loss")

    update_query = normalize_whitespace("UPDATE boxers SET fights = fights + 1 WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])
    actual_args = mock_cursor.execute.call_args_list[1][0][1]

    assert actual_query == update_query
    assert actual_args == (1,)

def test_update_boxer_stats_invalid_result():
    """Test error when invlaid fight result. E.G., not "win" or "loss"
    
    """

    with pytest.raises(ValueError, match="Invalid result: tie. Expected 'win' or 'loss'."):
        update_boxer_stats(1, "tie")

def test_update_boxer_stats_invalid_id(mock_cursor):
    """Test error when invalid boxer ID.
    
    """

    mock_cursor.fetchone.return_value = None
    with pytest.raises(ValueError, match="Boxer with ID 999 not found."):
        update_boxer_stats(999, "win")