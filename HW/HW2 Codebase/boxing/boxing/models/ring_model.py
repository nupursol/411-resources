import logging
import math
from typing import List

from boxing.models.boxers_model import Boxer, update_boxer_stats
from boxing.utils.logger import configure_logger
from boxing.utils.api_utils import get_random


logger = logging.getLogger(__name__)
configure_logger(logger)


class RingModel:
    """
    manages a list of boxers, allows two boxers to enter the ring and facilitates the fight
    between them

    attributes:
        ring (List[Boxer]): list of boxers currently in the ring
    """
    def __init__(self):
        """ Initializes an empty ring with no boxers"""
        self.ring: List[Boxer] = []

    def fight(self) -> str:
        """
        simulates a fight between two boxers in the ring and the winner is determined based
        on their fighting skills the stats of both boxers are updated after the fight

        returns:
            str: name of winning boxer
        raises:
            ValueError: if there are fewer than two boxers in the ring
        """
        logger.info("Attempting to simulate a fight between the boxers in the ring")

        if len(self.ring) < 2:
            logger.error("There must be two boxers to start a fight.")
            raise ValueError("There must be two boxers to start a fight.")

        boxer_1, boxer_2 = self.get_boxers()

        logger.info(f"Fight started between {boxer_1.name} and {boxer_2.name}.")

        skill_1 = self.get_fighting_skill(boxer_1)
        skill_2 = self.get_fighting_skill(boxer_2)

        # Compute the absolute skill difference
        # And normalize using a logistic function for better probability scaling
        delta = abs(skill_1 - skill_2)
        normalized_delta = 1 / (1 + math.e ** (-delta))

        random_number = get_random()

        if random_number < normalized_delta:
            winner = boxer_1
            loser = boxer_2
        else:
            winner = boxer_2
            loser = boxer_1

        update_boxer_stats(winner.id, 'win')
        update_boxer_stats(loser.id, 'loss')

        self.clear_ring()

        logger.info(f"Fight sim finished. {winner.name} won.")

        return winner.name

    def clear_ring(self):
        """ clears ring """
        logger.info("Attempting to clear the ring")

        if not self.ring:
            logger.warning("The ring is already clear")
            return
        self.ring.clear()
        logger.info("Ring cleared")

    def enter_ring(self, boxer: Boxer):
        """
        adds a boxer to the ring with max of two at a time

        args:
            boxer (Boxer): boxer to add to ring
        raises:
            TypeError: if boxer is not an instance of the Boxer class
            ValueError: if ring is already full
        """
        logger.info("Attempting to add boxer to the ring")

        if not isinstance(boxer, Boxer):
            logger.error(f"Invalid type: Expected 'Boxer', got '{type(boxer).__name__}'.")
            raise TypeError(f"Invalid type: Expected 'Boxer', got '{type(boxer).__name__}'")

        if len(self.ring) >= 2:
            logger.warning("Ring is full, cannot add more boxers.")
            raise ValueError("Ring is full, cannot add more boxers.")

        self.ring.append(boxer)
        logger.info(f"{boxer.name} was added to the ring.")

    def get_boxers(self) -> List[Boxer]:
        """
        gets the boxers currently in the ring

        returns:
            List[Boxer]: a list with the two boxers in the ring
        """
        logger.info("Attempting to get list of boxers in the ring")

        if not self.ring:
            logger.warning("No boxers currently in the ring.")
            pass
        else:
            logger.info("Got list of boxers in the ring successfully")
            pass

        return self.ring

    def get_fighting_skill(self, boxer: Boxer) -> float:
        """
        calculates fighting skill of boxer based on weight, reach and age

        args:
            boxer (Boxer): boxer whose skill is being calculated
        returns:
            float: calculated fighting skill of boxer
        """
        logger.info(f"Attempting to calculate boxer '{boxer.name}' fighting skill")

        # Arbitrary calculations
        age_modifier = -1 if boxer.age < 25 else (-2 if boxer.age > 35 else 0)
        skill = (boxer.weight * len(boxer.name)) + (boxer.reach / 10) + age_modifier

        logger.info(f"Calculated fighting skill for boxer '{boxer.name}': {skill}")
        return skill
