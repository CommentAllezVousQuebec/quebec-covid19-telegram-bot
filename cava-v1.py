#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from typing import Dict

from elasticsearch import Elasticsearch
from telegram import ReplyKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)

es = Elasticsearch(
    cloud_id="commentallezvous:bm9ydGhhbWVyaWNhLW5vcnRoZWFzdDEuZ2NwLmVsYXN0aWMtY2xvdWQuY29tJDEzYjc5N2YxMjUzOTQ5MWM4YzlmZGM2Yzk2OTBmNTc1JDhkMjQ3NWY1NTM3YzRjZDk4NWZiNTExOTUxZGI1MzQ2",
    http_auth=("elastic", "1EozbFBlK46bqpaJ1ZOzbelo"),
)

doc = {
    'author':    'kimchy',
    'text':      'Elasticsearch: cool. bonsai cool.',
    'timestamp': datetime.now(),
}

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)

reply_keyboard = [
    ['Humeur', 'Besoin'],
    ['Température', 'Symptôme'],
    ['Terminer']
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

reply_keyboard1 = [
    ['Toux'],
    ['Grande fatigue'],
    ['Difficulté respiratoire']
]
markup1 = ReplyKeyboardMarkup(reply_keyboard1, one_time_keyboard=True)


def facts_to_str(user_data):
    facts = []

    for key, value in user_data.items():
        facts.append(f'{key} - {value}')

    return "\n".join(facts).join(['\n', '\n'])


def start(update, context: Dict):
    context.update({
        'Prénom': 'François',
        'Téléphone': '+1-418-999-9999',
        'Age': '50+',
        'Statut': 'revient de voyage',
    })
    update.message.reply_text("Monsieur François, 50+, revient de voyage\n+1-418-999-9999",
                              reply_markup=markup)

    return CHOOSING


def regular_choice(update, context):
    text = update.message.text
    context.user_data['choice'] = text
    update.message.reply_text(f'Réponses obtenues : {text.lower()}? ')

    return TYPING_REPLY


def custom_choice(update, context):
    update.message.reply_text('Vos symptomes', reply_markup=markup1)

    return TYPING_CHOICE


def received_information(update, context):
    user_data = context.user_data
    text = update.message.text
    category = user_data['choice']
    user_data[category] = text
    del user_data['choice']

    update.message.reply_text(f"Les réponses:{facts_to_str(user_data)}",
                              reply_markup=markup)

    return CHOOSING


def done(update, context):
    user_data = context.user_data
    if 'choice' in user_data:
        del user_data['choice']

    update.message.reply_text(f"Les réponses finales obtenues:{facts_to_str(user_data)}")

    logging.warning(f'Update "{update}" user_data "{context.user_data}"')

    # 'timestamp': datetime.now()

    document = context.user_data
    document['timestamp'] = datetime.now()

    res = es.index(index="test-index", body=document)
    print(res['result'])

    user_data.clear()
    return ConversationHandler.END


def error(update, context):
    """Log Errors caused by Updates."""
    logging.warning(f'Update "{update}" caused error "{context.error}"')


def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater("1030659168:AAFEhWhl7AYQo1p59KcaSM4NmVaeTn8PONM", use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    dispatcher.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                CHOOSING:      [
                    MessageHandler(Filters.regex('^(Humeur|Besoin|Température)$'), regular_choice),
                    MessageHandler(Filters.regex('^Symptôme$'), custom_choice)
                ],
                TYPING_CHOICE: [
                    MessageHandler(Filters.text, regular_choice)
                ],
                TYPING_REPLY:  [
                    MessageHandler(Filters.text, received_information),
                ],
            },
            fallbacks=[MessageHandler(Filters.regex('^Terminer$'), done)]
        )
    )

    # log all errors
    dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
