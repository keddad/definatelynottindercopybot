from dataclasses import dataclass
from loguru import logger
from pymongo import MongoClient

mongo = MongoClient("mongodb://pair_mongodb:27017/").db.users

ORIENTATION_INTERPRETATION = {
    '🏳️‍🌈': "G",
    '👫': "S",
    'Би': "A"
}

GENDER_INTERPRETATION = {
    'Парень': 'M',
    'Девушка': 'F',
    "¯\_(ツ)_/¯": 'A'
}

ORIENTATION_GENDER_TO_TAGET = {
    "S": {
        "M": ["F"],
        "F": ["M"],
        "A": ["F", "M", "A"]
    },
    "G": {
        "M": ["M"],
        "F": ["F"],
        "A": ["F", "M", "A"]
    },
    "A": {
        "M": ["F", "M", "A"],
        "F": ["F", "M", "A"],
        "A": ["F", "M", "A"]
    }
}


@dataclass
class CachedUser:
    name: str
    chat_id: int
    photo_id: str
    gender: str
    bio: str
    orientation: str


def create_or_update_user(bio: CachedUser):
    if mongo.find({"chat_id": bio.chat_id}).count() > 0:
        mongo.update_one({"chat_id": bio.chat_id}, {"$set": {"bio": bio.bio, "name": bio.name,
                                                             "photo_id": bio.photo_id, "gender": bio.gender, "orientation": bio.orientation}})
        logger.debug("Updated someone's bio")
    else:
        mongo.insert_one(
            {
                "chat_id": bio.chat_id,
                "photo_id": bio.photo_id,
                "name": bio.name,
                "gender": bio.gender,
                "orientation": bio.orientation,
                "bio": bio.bio,
                "loves": [],
                "seen": [bio.chat_id]
            }
        )

        logger.debug("Created new bio")


def get_new_candidate(to: int):
    user = mongo.find_one({"chat_id": to})

    for elem in mongo.find({"gender": {"$in": ORIENTATION_GENDER_TO_TAGET[user["orientation"]][user["gender"]]}}):
        if elem["chat_id"] not in user["seen"]:
            return elem

    return None

def people_match(a: int, b: int, loved: bool):
    if loved:
        mongo.update_one({"chat_id": a}, {"$push": {"seen": b, "loves": b}})
    else:
        mongo.update_one({"chat_id": a}, {"$push": {"seen": b}})

def is_it_match(a, b):
    a = mongo.find_one({"chat_id": a})
    b = mongo.find_one({"chat_id": b})

    return a["chat_id"] in b["loves"] and b["chat_id"] in a["loves"]