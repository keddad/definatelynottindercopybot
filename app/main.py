import telebot
from telebot import types
import os
from loguru import logger
from typing import Dict
from utils import *

API_TOKEN = os.environ["token"]

bot = telebot.TeleBot(API_TOKEN)

user_cache: Dict[int, CachedUser] = {}
id_to_match = {}


@bot.message_handler(commands=['start', 'change'])
def send_welcome(message):
    msg = bot.reply_to(
        message,
        "Привет! Сейчас мы будем тебя шипперить. Как тебя зовут? (Ты в любой момент сможешь обновить информацию командой /change)")
    bot.register_next_step_handler(msg, reg_get_name)


def reg_get_name(message):
    chat_id = message.chat.id
    name = message.text
    user_cache[chat_id] = CachedUser(name, chat_id, "", "", "", "")
    msg = bot.reply_to(message, 'Расскажи о себе')
    bot.register_next_step_handler(msg, reg_get_bio)


def reg_get_bio(message):
    chat_id = message.chat.id

    if chat_id not in user_cache:
        bot.reply_to(message, "Что то сломалось, тебе придется начать сначала. Напиши /start")
        return

    user_cache[chat_id].bio = message.text

    if message.text is None or message.text == "":
        msg = bot.reply_to(message, 'Био должно быть текстом.')
        bot.register_next_step_handler(msg, reg_get_bio)

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add(*GENDER_INTERPRETATION.keys())
    msg = bot.reply_to(
        message, 'Отлично, давай поговорим о твоем поле:', reply_markup=markup)
    bot.register_next_step_handler(msg, reg_get_sex)


def reg_get_sex(message):
    chat_id = message.chat.id

    if chat_id not in user_cache:
        bot.reply_to(message, "Что то сломалось, тебе придется начать сначала. Напиши /start")
        return

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

    if chat_id not in user_cache:
        bot.reply_to(message, "Что то сломалось, тебе придется начать сначала. Напиши /start")
        return

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

    if chat_id not in user_cache:
        bot.reply_to(message, "Что то сломалось, тебе придется начать сначала. Напиши /start")
        return

    if message.content_type != "photo":
        msg = bot.reply_to(message, "Это не фоточка, а мне нужна фоточка")
        bot.register_next_step_handler(msg, reg_get_photo)
        return

    user_cache[chat_id].photo_id = message.photo[0].file_id
    create_or_update_user(user_cache[chat_id])
    del user_cache[chat_id]
    get_option(message)


@bot.message_handler(commands=['next'])
def get_option(message):
    try:
        candidate = get_new_candidate(message.chat.id)
    except IndexError:
        bot.reply_to(message, "Что то сломалось, тебе придется начать сначала. Напиши /start")
        return

    if candidate is None:
        logger.debug(f"No matches for {message.from_user.username}")
        bot.send_message(
            message.chat.id, "Нет подходящих кандидатов. Попробуй через часик комадной /next")
        return

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add("❤️", "💔")

    msg = bot.send_photo(
        message.chat.id, candidate["photo_id"], caption=f"{candidate['name']}\n{candidate['bio']}", reply_markup=markup)

    logger.debug(f"Propose {message.from_user.username} & {candidate['chat_id']}")

    id_to_match[message.chat.id] = candidate["chat_id"]
    bot.register_next_step_handler(msg, analyze_option)


def analyze_option(message):
    if message.text not in ["❤️", "💔"]:

        if message.text == "/change":
            msg = bot.reply_to(
                message, "Хорошо, мы идем все менять. Как тебя зовут?")
            bot.register_next_step_handler(msg, reg_get_name)
            return

        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add("❤️", "💔")
        msg = bot.reply_to(
            message, "Нажми на кнопочку, пожалуйста", reply_markup=markup)
        bot.register_next_step_handler(msg, analyze_option)
        return

    people_match(message.chat.id,
                 id_to_match[message.chat.id], message.text == "❤️")

    if is_it_match(message.chat.id, id_to_match[message.chat.id]):
        logger.debug(
            f"Match between {id_to_match[message.chat.id]} and {message.from_user.id}")
        bot.send_message(
            message.chat.id,
            f"It's a match! Пиши скорее [\"{bot.get_chat(id_to_match[message.chat.id]).first_name}\"](tg://user?id={id_to_match[message.chat.id]})",
            parse_mode="Markdown"
        )

        bot.send_message(
            id_to_match[message.chat.id],
            f"It's a match! Пиши скорее [\"{message.from_user.first_name}\"](tg://user?id={id_to_match[message.chat.id]})",
            parse_mode="Markdown"
        )

    get_option(message)


bot.polling()
