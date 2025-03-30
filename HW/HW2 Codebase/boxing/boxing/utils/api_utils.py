import logging
import os
import requests

from boxing.utils.logger import configure_logger


logger = logging.getLogger(__name__)
configure_logger(logger)


RANDOM_ORG_URL = os.getenv("RANDOM_ORG_URL",
                           "https://www.random.org/decimal-fractions/?num=1&dec=2&col=1&format=plain&rnd=new")


def get_random() -> float:
    """
    fetches a random decimal number from random.org

    Returns:
        float: random decimal between 0 and 1 (found by going to the url)
    raises:
        RuntimeError: if request to random.org fails or times out
        ValueError: if response from random.org is not a valid float
    """
    try:
        #Log the request to random.org
        logger.info(f"Fetching random decimal from {RANDOM_ORG_URL}")

        response = requests.get(RANDOM_ORG_URL, timeout=5)

        # Check if the request was successful
        response.raise_for_status()

        random_number_str = response.text.strip()
        logger.info(f"Recieved response from random.org: {random_number_str}")

        try:
            random_number = float(random_number_str)
        except ValueError:
            logger.error(f"Invalid response from random.org: {random_number_str}")
            raise ValueError(f"Invalid response from random.org: {random_number_str}")
        
        logger.info(f"Converted response to float: {random_number}")
        return random_number

    except requests.exceptions.Timeout:
        logger.error(f"Request to random.org timed out")
        raise RuntimeError("Request to random.org timed out.")

    except requests.exceptions.RequestException as e:
        logger.error(f"Request to random.org failed: {e}")
        raise RuntimeError(f"Request to random.org failed: {e}")
