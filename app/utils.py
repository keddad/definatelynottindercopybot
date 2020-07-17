from dataclasses import dataclass
from loguru import logger
from pymongo import MongoClient

mongo = MongoClient("mongodb://pair_mongodb:27017/").db.users

ORIENTATION_INTERPRETATION = {
    '🏳️‍🌈': "G",
    '👫': "S",
    'Лава': "A"
}

GENDER_INTERPRETATION = {
    'Парень': 'M',
    'Девушка': 'F',
    "Лава": '?'
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
                "bio": bio.bio
            }
        )

        logger.debug("Created new bio")
