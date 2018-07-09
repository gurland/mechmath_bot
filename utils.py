#!/usr/bin/env python3
import re
from datetime import datetime
from html.parser import HTMLParser
import logging

import asyncio
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher

import config


my_bot = Bot(token=config.bot_token, proxy=config.PROXY_URL, proxy_auth=config.PROXY_AUTH)
dp = Dispatcher(my_bot)


class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


async def bot_name(bot):
    return (await bot.me).username

loop = asyncio.get_event_loop()
my_bot_name = loop.run_until_complete(bot_name(my_bot))


def divide_text(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def curr_time():
    return datetime.now().strftime('%d/%m/%Y %H:%M:%S')


def commands_handler(cmnds, inline=False):
    def wrapped(message: types.Message):
        if not message.text:
            return False
        split_message = re.split(r'[^\w@/]', message.text.lower())
        if not inline:
            s = split_message[0]
            return ((s in cmnds)
                    or (s.endswith(my_bot_name) and s.split('@')[0] in cmnds))
        else:
            return any(cmnd in split_message
                       or cmnd + my_bot_name in split_message
                       for cmnd in cmnds)

    return wrapped


def user_info(user):
    # Required fields
    user_id = str(user.id)
    first_name = user.first_name
    # Optional fields
    last_name = ' ' + user.last_name if isinstance(user.last_name, str) else ''
    username = ', @' + user.username if isinstance(user.username, str) else ''
    language_code = ', ' + user.language_code if isinstance(user.language_code, str) else ''
    # Output
    return user_id + ' (' + first_name + last_name + username + language_code + ')'


def chat_info(chat):
    if chat.type == 'private':
        return 'private'
    else:
        return chat.type + ': ' + chat.title + ' (' + str(chat.id) + ')'


def error_log(text):
    logging.error(text)


def action_log(text):
    logging.info(text)


def user_action_log(message, text):
    logging.info("{}\nUser {} {}\n".format(chat_info(message.chat), user_info(message.from_user), text))


def command_with_delay(delay=10):
    def my_decorator(func):
        def wrapped(message):
            if message.chat.type != 'private':
                now = datetime.now().timestamp()
                diff = now - func.last_call if hasattr(func, 'last_call') else now
                if diff < delay:
                    user_action_log(message, "called {} after {} sec, delay is {}".format(func, round(diff), delay))
                    return
                func.last_call = now

            return func(message)

        return wrapped

    return my_decorator


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()
