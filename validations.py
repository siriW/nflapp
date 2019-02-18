import logging
import requests

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("validations")

VALID_SEASONS = [2014, 2015, 2016, 2017, 2018, 2019]
VALID_SEASON_TYPES = ["REG"]

def validate_season(season, app):
    INVALID_DATA = app.response_class(response="400 - Invalid season: valid seasons are : {}".
                                      format(",".join(str(s) for s in VALID_SEASONS)), status=400)
    try:
        season = int(season)
        if season not in VALID_SEASONS:
            return False, INVALID_DATA
    except TypeError:
        return False, INVALID_DATA
    return True, None

def validate_seasonType(seasonType, app):
    if seasonType not in VALID_SEASON_TYPES:
        return False, app.response_class(response="400 - Invalid seasonType: valid seasonTypes are : {}".
                                  format(",".join(VALID_SEASON_TYPES)), status=400)
    return True, None

def validate_team(team, app, VALID_TEAMS, season):
    if team not in VALID_TEAMS:
        return False, app.response_class(response="400 - Invalid team: valid teams for the season:{} are : {}".
                                  format(season, ",".join(VALID_TEAMS)), status=400)
    return True, None