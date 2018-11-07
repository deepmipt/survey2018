import html
import json
import random
from pathlib import Path

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

with open('config.json', encoding='utf-8') as f:
    config = json.load(f)

DATA_PATH = Path(config['DATA_PATH']).expanduser().resolve()
LOG_PATH = Path(config['LOG_PATH']).expanduser().resolve()
TOKEN = config['TOKEN']
PROXY = config['PROXY']


data = []
if DATA_PATH.is_dir():
    for p in DATA_PATH.glob('**/*.json'):
        with p.open(encoding='utf-8') as f:
            data += json.load(f)
elif DATA_PATH.is_file():
    with DATA_PATH.open(encoding='utf-8') as f:
        data = json.load(f)
else:
    raise RuntimeError(f'{DATA_PATH} is not there')
# data = {item['chat_id']: item for item in data}

logfile = LOG_PATH.open('a', encoding='utf-8')


if PROXY is not None:
    telebot.apihelper.proxy = {'https': PROXY}

bot = telebot.TeleBot(TOKEN)


def send(chat):
    d = random.choice(data)
    msg_count = len(d['messages'])
    msg_count = random.randint(min(3, msg_count), msg_count)
    if d['messages'][msg_count-1]['speaker'] != 'Operator':
        msg_count += 1
    messages = d['messages'][:msg_count]
    msg_count = len(messages)
    response = "\n".join([f'<b>{m["speaker"].upper()}</b>: ' + html.escape(m['utterance'].replace('__eou__', ''))
                          for m in messages])

    markup = InlineKeyboardMarkup()

    button1 = InlineKeyboardButton('Осмысленно', callback_data=f'1\t{d["chat_id"]}\t{msg_count}')
    button2 = InlineKeyboardButton('Не осмысленно', callback_data=f'0\t{d["chat_id"]}\t{msg_count}')
    markup.add(button1, button2)

    bot.send_message(chat.id, response, reply_markup=markup, parse_mode='HTML')


@bot.message_handler(commands=['start'])
def start_message(message):
    send(message.chat)


@bot.callback_query_handler(lambda call: True)
def handle_callback(call):
    chat = call.from_user
    meaningful, chat_id, msg_count = call.data.split('\t')
    callback_data = {
        'meaningful': bool(int(meaningful)),
        'chat_id': chat_id,
        'msg_count': msg_count,
        'tg_user': {
            'id': chat.id,
            'username': getattr(chat, 'username', None),
            'first_name': getattr(chat, 'first_name', None),
            'last_name': getattr(chat, 'last_name', None)
        }
    }
    callback_data = json.dumps(callback_data, ensure_ascii=False)
    print(callback_data)
    print(callback_data, file=logfile, flush=True)
    send(call.from_user)


# @bot.message_handler()
# def start_message(message):
#     chat_id = message.chat.id
#     bot.send_message(chat_id, '', parse_mode="Markdown")


bot.polling()
