import pytest
import requests

from boxing.utils.api_utils import get_random

"""mocked random decimal response"""
RANDOM_DECIMAL = 0.42

@pytest.fixture
def mock_random_org(mocker):
    """mock requests.get response for random.org"""
    mock_response = mocker.Mock()
    mock_response.text = f"{RANDOM_DECIMAL}"  # simulates valid response
    mocker.patch("requests.get", return_value=mock_response)
    return mock_response

def test_get_random(mock_random_org):
    """test takes a random decimal number from random.org."""
    result = get_random()
    assert result == RANDOM_DECIMAL, f"Expected {RANDOM_DECIMAL}, but got {result}"
    requests.get.assert_called_once_with(
        "https://www.random.org/decimal-fractions/?num=1&dec=2&col=1&format=plain&rnd=new", timeout=5
    )

def test_get_random_request_failure(mocker):
    """test for request failure when calling random.org."""
    mocker.patch("requests.get", side_effect=requests.exceptions.RequestException("Connection error"))
    with pytest.raises(RuntimeError, match="Request to random.org failed: Connection error"):
        get_random()

def test_get_random_timeout(mocker):
    """test for timeout when calling random.org."""
    mocker.patch("requests.get", side_effect=requests.exceptions.Timeout)
    with pytest.raises(RuntimeError, match="Request to random.org timed out."):
        get_random()

def test_get_random_invalid_response(mock_random_org):
    """test for invalid response from random.org."""
    mock_random_org.text = "invalid_response"
    with pytest.raises(ValueError, match="Invalid response from random.org: invalid_response"):
        get_random()
