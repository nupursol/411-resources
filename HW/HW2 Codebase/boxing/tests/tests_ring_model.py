import pytest
import math
import re
from contextlib import contextmanager

from boxing.models.boxers_model import Boxer, update_boxer_stats
from boxing.models.ring_model import RingModel
from boxing.utils.api_utils import get_random

######################################################
#    Utility Functions
######################################################

def normalize_whitespace(text: str) -> str:
     """normalize whitespace to a single space for SQL comparison"""
     return re.sub(r"\s+", " ", text).strip()

######################################################
#    SQL Mocking Fixture
######################################################
# this fixture creates a fake SQL connection and cursor
# the fake_get_db_connection function will be patched into the module where update_boxer_stats is defined
# this allows me to capture the SQL queries executed during update_boxer_stats calls
# we assume that update_boxer_stats, when given a "win" result, executes:
#     UPDATE boxers SET wins = wins + 1 WHERE id = ?

class FakeCursor:
     def __init__(self):
        self.calls = [] 

     def execute(self, query, args):
          self.calls.append((query, args))

     def fetchone(self):
          return None

     def fetchall(self):
          return []

     def commit(self):
          pass

class FakeConnection:
     def __init__(self, cursor):
          self._cursor = cursor

     def cursor(self):
          return self._cursor

     def commit(self):
          pass

@contextmanager
def fake_db_connection():
     """context manager that yields a fake connection using our FakeCursor"""
     fake_cursor = FakeCursor()
     fake_conn = FakeConnection(fake_cursor)
     yield fake_conn

@pytest.fixture
def mock_db_cursor(monkeypatch):
     """ patches the get_db_connection function in boxing.models.boxers_model so that
     when update_boxer_stats is called it uses our fake connection
     Returns the FakeCursor instance so tests can inspect the executed SQL calls """
     
     # since update_boxer_stats is defined in boxing.models.boxers_model
     # patch that module’s get_db_connection
     # we want every call to get_db_connection to return the same fake connection so we can capture all calls
     fake_cursor = FakeCursor()
     fake_conn = FakeConnection(fake_cursor)
     @contextmanager
     def fake_get_db_connection():
          yield fake_conn

     monkeypatch.setattr("boxing.models.boxers_model.get_db_connection", fake_get_db_connection)
     return fake_cursor
    # Using monkeypatch to override get_db_connection ensures that my tests don't interact 
    # with a real database which allows us to isolate the logic being tested while verifying 
    # that the correct SQL queries are executed


######################################################
#    Other Fixtures (Boxers and Ring)
######################################################

@pytest.fixture
def ring():
     """provides a fresh RingModel for each test"""
     return RingModel()

@pytest.fixture
def boxer1():
     """dummy boxer with mid-range attributes"""
     return Boxer(id=1, name="Fighter A", age=30, weight=150, reach=70, height=72)

@pytest.fixture
def boxer2():
     """another dummy boxer with similar attributes for a balanced fight"""
     return Boxer(id=2, name="Fighter B", age=30, weight=150, reach=70, height=72)

######################################################
#    Fight Tests
######################################################

def test_fight_insufficient_boxers(ring):
     """fight() should raise ValueError if less than two boxers are in the ring"""
     with pytest.raises(ValueError, match="There must be two boxers to start a fight."):
          ring.fight()

def test_fight_boxer1_wins(monkeypatch, ring, boxer1, boxer2, mock_db_cursor):
     """ when two boxers are in the ring and get_random returns a value lower than the difference between skills,
     boxer1 wins. Also checking that update_boxer_stats executes the correct SQL queries"""

     ring.enter_ring(boxer1)
     ring.enter_ring(boxer2)

     # for equal skills difference is 0 so normalized difference = 0.5
     # returning 0.3 (< 0.5) should let the first boxer win
     monkeypatch.setattr("boxing.models.ring_model.get_random", lambda: 0.3)
     # Define a fetchone side effect that dynamically returns boxer_id -THIS WAS CAUSING SO MANY ERRORS BECAUSE FETCHONE WAS DEFAULTING TO NONE
     def fetchone_side_effect():
        return (mock_db_cursor.calls[-1][1][0],)  # Extract boxer_id from last query args

     mock_db_cursor.fetchone = fetchone_side_effect  # Assign side effect
     winner_name = ring.fight()

     # expected SQL queries (adjust these if your actual queries differ):
     expected_win_query = normalize_whitespace("UPDATE boxers SET fights = fights + 1, wins = wins + 1 WHERE id = ?")
     expected_loss_query = normalize_whitespace("UPDATE boxers SET fights = fights + 1 WHERE id = ?")
     # verify the fight outcome
     assert winner_name == boxer1.name, "Expected Fighter A to win"
     # verify that update_boxer_stats was called twice and the SQL queries match
     # we expect two calls: one for winner and one for loser
     assert len(mock_db_cursor.calls) == 4, "Expected four SQL executions: two SELECT and two UPDATE"
     update_queries = [(q, a) for q, a in mock_db_cursor.calls if q.startswith("UPDATE")]
     win_query, win_args = update_queries[0]  # First update should be the winner
     loss_query, loss_args = update_queries[1]  # Second update should be the loser
     assert normalize_whitespace(win_query) == expected_win_query, "Win query did not match expected SQL"
     assert normalize_whitespace(loss_query) == expected_loss_query, "Loss query did not match expected SQL"  
     # after the fight, the ring should be cleared
     assert ring.ring == [], "he ring was not cleared after the fight"


def test_fight_boxer2_wins(monkeypatch, ring, boxer1, boxer2, mock_db_cursor):
     """when two boxers are in the ring and get_random returns a value greater than or equal to 0.5
     boxer2 wins also verifyign sql"""
     ring.enter_ring(boxer1)
     ring.enter_ring(boxer2)

     monkeypatch.setattr("boxing.models.ring_model.get_random", lambda: 0.7)
     # Define a fetchone side effect that dynamically returns boxer_id
     def fetchone_side_effect():
        return (mock_db_cursor.calls[-1][1][0],)  # Extract boxer_id from last query args
     mock_db_cursor.fetchone = fetchone_side_effect  # Assign side effect
     winner_name = ring.fight()

     expected_win_query = normalize_whitespace("UPDATE boxers SET fights = fights + 1, wins = wins + 1 WHERE id = ?")
     expected_loss_query = normalize_whitespace("UPDATE boxers SET fights = fights + 1 WHERE id = ?")
     assert winner_name == boxer2.name, "Expected fighter B to win"
     assert len(mock_db_cursor.calls) == 4, "Expected four SQL executions: two SELECT and two UPDATE"
     update_queries = [(q, a) for q, a in mock_db_cursor.calls if q.startswith("UPDATE")]
     win_query, win_args = update_queries[0]  # First update should be the winner
     loss_query, loss_args = update_queries[1]  # Second update should be the loser
     assert normalize_whitespace(win_query) == expected_win_query, "Win query did not match expected SQL"
     assert normalize_whitespace(loss_query) == expected_loss_query, "Loss query did not match expected SQL"  
     assert ring.ring == [], "ring was not cleared after the fight"


######################################################
#    Clear Ring Tests
######################################################

def test_clear_ring_not_empty(ring, boxer1):
     """clear_ring() should empty the ring if boxers are present"""
     ring.enter_ring(boxer1)
     assert len(ring.ring) == 1
     ring.clear_ring()
     assert ring.ring == [], "ring not cleared properly"

def test_clear_ring_empty(ring):
     """clear_ring() should work  when the ring is already empty"""
     ring.clear_ring()
     assert ring.ring == []

######################################################
#    Enter Ring Tests
######################################################

def test_enter_ring_valid(ring, boxer1):
     """enter_ring() should add a valid Boxer to the ring"""
     ring.enter_ring(boxer1)
     assert ring.ring == [boxer1]

def test_enter_ring_invalid_type(ring):
     """enter_ring() should raise TypeError if a non-Boxer is provided"""
     with pytest.raises(TypeError, match="Invalid type: Expected 'Boxer'"):
          ring.enter_ring("Not a boxer")

def test_enter_ring_full(ring, boxer1, boxer2):
     """enter_ring() should raise ValueError if trying to add third boxer"""
     ring.enter_ring(boxer1)
     ring.enter_ring(boxer2)
     with pytest.raises(ValueError, match="Ring is full"):
          ring.enter_ring(boxer1) # Attempt to add third


######################################################
#    Get Boxers & Fighting Skill Tests
######################################################

def test_get_boxers(ring, boxer1, boxer2):
     """get_boxers() should return list of boxers currently in the ring"""
     ring.enter_ring(boxer1)
     ring.enter_ring(boxer2)
     boxers = ring.get_boxers()
     assert boxers == [boxer1, boxer2]

def test_get_fighting_skill(ring, boxer1):
     """get_fighting_skill() should correctly calculate the fighting skill
     calculation: (weight * len(name)) + (reach / 10) + age_modifier,
     where age_modifier is:-1 if age < 25, -2 if age > 35, 0 otherwise"""
     # for boxer1 age is 30 so modifier is 0
     expected_skill = (boxer1.weight * len(boxer1.name)) + (boxer1.reach / 10)
     calculated_skill = ring.get_fighting_skill(boxer1)
     assert math.isclose(calculated_skill, expected_skill), f"Expected skill {expected_skill}, got {calculated_skill}"

