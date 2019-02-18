import logging
import os

import pymongo
import requests
from flask import Flask, json, request
import validations

# client = pymongo.MongoClient("mongodb+srv://{}:{}@cluster0-pykhk.mongodb.net/test?retryWrites=true".
#                              format(os.environ["MONGO_DB_USER"], os.environ["MONGO_DB_PASSWORD"]
#                                     ))

client = pymongo.MongoClient()

db = client.get_database("sportsfeed_db")
sportsfeed_collection = db.get_collection("sportsfeed_collection")

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("app")

app = Flask(__name__)

BASE_URL = "https://api.ngs.nfl.com/league"

def get_teams(season):
    return [team["abbr"] for team in requests.get(BASE_URL + "/teams", params = {"season" : season}).json()]

@app.route("/ingest")
def ingest():
    logger.info("request: {}".format(request.args))

    season = int(request.args.get("season"))
    seasonType = str(request.args.get("seasonType"))

    check, response = validations.validate_season(season, app)
    if not check:
        return response

    check, response = validations.validate_seasonType(seasonType, app)
    if not check:
        return response

    response = requests.get(BASE_URL+"/schedule", params={"season" : season, "seasonType" : seasonType})

    data = response.json()

    record_ids = sportsfeed_collection.insert_many(data)
    logger.info("Records inserted: {}".format(len(record_ids.inserted_ids)))

    message = {"message": "Number of records ingested: {}".format(len(record_ids.inserted_ids))}

    return app.response_class(response=json.dumps(message), status=200, mimetype='application/json')

def get_bye_weeks(team, season):
    # Team played weeks
    play_week_docs = sportsfeed_collection.find(
        {"$and": [{"$or": [{"homeTeamAbbr": {"$eq": team}}, {"visitorTeamAbbr": {"$eq": team}}]}, {"season": {"$eq": season}}]})
    play_weeks = []
    for week in play_week_docs:
        if week["week"] not in play_weeks:
            play_weeks.append(week["week"])

    logger.debug("play weeks: {}".format(play_weeks))

    # Teams not played games
    byeweek_docs = sportsfeed_collection.find(
        {"$and": [{"homeTeamAbbr": {"$ne": team}}, {"visitorTeamAbbr": {"$ne": team}}, {"season": {"$eq": season}}]})
    byeweeks = []
    for byeweek in byeweek_docs:
        if byeweek["week"] not in play_weeks and byeweek["week"] not in byeweeks:
            byeweeks.append(byeweek["week"])

    print("Bye week: {}".format(byeweeks))

    response = {}
    response["team"] = team
    if not byeweeks or len(byeweeks)> 1:
        response["byeweek"] = 0
    else:
        response["byeweek"] = byeweeks[0]
    return response


def get_bye_weeks_avg(team, season, byeweek):
    # Team played weeks

    play_week_docs = sportsfeed_collection.find(
        {"$and": [{"$or": [{"homeTeamAbbr": {"$eq": team}}, {"visitorTeamAbbr": {"$eq": team}}]}
            , {"season": {"$eq": season}}, {"week": {"$gt": byeweek}}]})

    play_weeks = []
    total_points = 0

    for game in play_week_docs:
        if game["week"] not in play_weeks:
            play_weeks.append(game["week"])

        if game["homeTeamAbbr"] == team:
            total_points += game["score"]["homeTeamScore"]["pointTotal"]
        elif game["visitorTeamAbbr"] == team:
            total_points += game["score"]["visitorTeamScore"]["pointTotal"]

    print("Team :{}".format(team))
    print("Total points: {}".format(total_points))
    print("Total weeks: {}".format(len(play_weeks)))
    average =  float(total_points) / float(len(play_weeks))

    response = {}
    response["team"] = team
    response["average"] = average

    return response

@app.route("/byeweek")
def byeweek():
    logger.info("request: {}".format(request.args))

    season = int(request.args.get("season"))
    team_alias = request.args.get("team_alias")

    check, response = validations.validate_season(season, app)
    if not check:
        return response

    VALID_TEAMS = get_teams(season)

    r_response = []

    if team_alias:
        check, response = validations.validate_team(team_alias, app, VALID_TEAMS, season)
        if not check:
            return response

        r_response.append(get_bye_weeks(team_alias, season))
    else:
        for team in VALID_TEAMS:
            r_response.append(get_bye_weeks(team, season))

    logger.debug("season : {}, response: {}".format(season, r_response))
    return app.response_class(response=json.dumps(r_response), status=200, mimetype='application/json')


@app.route("/average")
def average():
    logger.info("request: {}".format(request.args))

    team_alias = request.args.get("team_alias")
    season = int(request.args.get("season"))
    period = request.args.get("period")

    check, response = validations.validate_season(season, app)
    if not check:
        return response

    VALID_TEAMS = get_teams(season)

    if team_alias:
        check, response = validations.validate_team(team_alias, app, VALID_TEAMS, season)
        if not check:
            return response

        byeweek = get_bye_weeks(team_alias, season)["byeweek"]

        if not byeweek:
            return app.response_class(response="400 - No byeweek for the team: {}".format(team_alias), status=400)

        average = get_bye_weeks_avg(team_alias, season, byeweek)

        return app.response_class(response=json.dumps(average), status=200, mimetype='application/json')

    else:
        return app.response_class(response="400 - Missing data: team and/or team params are required", status=400)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)