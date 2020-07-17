import telebot
from telebot import types
import os
from typing import Dict
from utils import *


API_TOKEN = os.environ["token"]

bot = telebot.TeleBot(API_TOKEN)

user_cache: Dict[int, CachedUser] = {}


@bot.message_handler(commands=['start', 'change'])
def send_welcome(message):
    msg = bot.reply_to(
        message, "Привет! Сейчас мы будем тебя шипперить. Как тебя зовут? (Ты в любой момент сможешь обновить информацию командой /change)")
    bot.register_next_step_handler(msg, reg_get_name)


def reg_get_name(message):
    chat_id = message.chat.id
    name = message.text
    user_cache[chat_id] = CachedUser(name, chat_id, "", "", "", "")
    msg = bot.reply_to(message, 'Расскажи о себе')
    bot.register_next_step_handler(msg, reg_get_bio)


def reg_get_bio(message):
    chat_id = message.chat.id

    user_cache[chat_id].bio = message.text

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add(*GENDER_INTERPRETATION.keys())
    msg = bot.reply_to(
        message, 'Отлично, давай поговорим о твоем поле:', reply_markup=markup)
    bot.register_next_step_handler(msg, reg_get_sex)


def reg_get_sex(message):
    chat_id = message.chat.id

    if message.text not in GENDER_INTERPRETATION:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add(*GENDER_INTERPRETATION.keys())
        msg = bot.reply_to(
            message, "Нажми на кнопочку, пожалуйста", reply_markup=markup)
        bot.register_next_step_handler(msg, reg_get_sex)
        return

    user_cache[chat_id].gender = GENDER_INTERPRETATION[message.text]

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add(*ORIENTATION_INTERPRETATION.keys())
    msg = bot.reply_to(
        message, "А теперь о ориентации", reply_markup=markup)

    bot.register_next_step_handler(msg, reg_get_orientation)


def reg_get_orientation(message):
    chat_id = message.chat.id

    if message.text not in ORIENTATION_INTERPRETATION:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add(*ORIENTATION_INTERPRETATION.keys())
        msg = bot.reply_to(
            message, "Нажми на кнопочку, пожалуйста", reply_markup=markup)
        bot.register_next_step_handler(msg, reg_get_orientation)
        return

    user_cache[chat_id].orientation = ORIENTATION_INTERPRETATION[message.text]

    msg = bot.reply_to(
        message, "А теперь скинь мне свое фото. Если не хочешь скидывать себя, можешь скинуть фото с котиком, я пойму.")
    bot.register_next_step_handler(msg, reg_get_photo)


def reg_get_photo(message):
    chat_id = message.chat.id

    if message.content_type != "photo":
        msg = bot.reply_to(message, "Это не фоточка, а мне нужна фоточка")
        bot.register_next_step_handler(msg, reg_get_photo)
        return

    user_cache[chat_id].photo_id = message.photo[0].file_id

    msg = bot.reply_to(message, f"{user_cache[chat_id]}")

    create_or_update_user(user_cache[chat_id])
    del user_cache[chat_id]
    bot.register_next_step_handler(msg, get_option)


def get_option(message):
    bot.reply_to(message, "Haha!")


while True:
    try:
        bot.polling()
    except Exception as e:
        print(e)
