import html
import json
import random
from collections import defaultdict
from datetime import datetime
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

models_data = defaultdict(list)
for item in data:
    model = item['model']
    ex_iter = None if model in ['random', 'no_model'] else item['experiment_iter']
    item['id'] = f"{item['experiment_iter']}_{item['experiment_id']}"
    models_data[(model, ex_iter)].append(item)
data = models_data
del models_data

logfile = LOG_PATH.open('a', encoding='utf-8')


if PROXY is not None:
    telebot.apihelper.proxy = {'https': PROXY}

bot = telebot.TeleBot(TOKEN)


def send(chat):
    key = random.choice(list(data.keys()))
    d = random.choice(data[key])
    while len(d['messages']) < 3:
        d = random.choice(data[key])
    msg_count = len(d['messages'])
    msg_count = random.randint(min(3, msg_count), msg_count)
    if d['messages'][msg_count-1]['speaker'] != 'Operator':
        msg_count += 1
    messages = d['messages'][:msg_count]
    msg_count = len(messages)
    response = "\n".join([f'<b>{m["speaker"].upper()}</b>: ' + html.escape(m['utterance']
                                                                           .replace('__eou__', '')
                                                                           .replace('\\n', '\n'))
                         .replace('SN_TOKEN', '<i>ОТЧЕСТВО</i>')
                         .replace('FN_TOKEN', '<i>ИМЯ</i>')
                         .replace('N_TOKEN', '<i>ИМЯ</i>')
                         .replace('NUM_TOKEN', '<i>НОМЕР_КАРТЫ</i>')
                         .replace('PHONE_TOKEN', '<i>ТЕЛЕФОН</i>')
                          for m in messages])

    if len(response) > 4000:
        return send(chat)

    markup = InlineKeyboardMarkup()

    button1 = InlineKeyboardButton('Осмысленно', callback_data=f'1\t{d["chat_id"]}\t{msg_count}\t{d["id"]}')
    button2 = InlineKeyboardButton('Не осмысленно', callback_data=f'0\t{d["chat_id"]}\t{msg_count}\t{d["id"]}')
    markup.add(button1, button2)

    bot.send_message(chat.id, response, reply_markup=markup, parse_mode='HTML')


@bot.message_handler(commands=['start'])
def start_message(message):
    send(message.chat)


@bot.callback_query_handler(lambda call: True)
def handle_callback(call):
    chat = call.from_user
    try:
        meaningful, chat_id, msg_count, _id = call.data.split('\t')
    except:
        send(call.from_user)
        return
    callback_data = {
        'meaningful': bool(int(meaningful)),
        'chat_id': chat_id,
        'id': _id,
        'msg_count': msg_count,
        'time': str(datetime.now()),
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


bot.polling(none_stop=True)
