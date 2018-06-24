#!/usr/bin/env python3
import datetime
import random
import asyncio

import bs4
import pytz
import requests

import config
from utils import my_bot, action_log


def daily_weather():
    url = 'https://sinoptik.com.ru/погода-москва'
    r = requests.get(url)
    soup = bs4.BeautifulSoup(r.text, 'html.parser')

    temp = [soup.select('.temperature .p{}'.format(i))[0].getText() for i in range(3, 9)]
    status = [soup.select('.rSide .description')[i].getText() for i in range(2)]

    daily = '{}\n\n' \
            '`  Утром: {}C — {}C`\n' \
            '`   Днём: {}C — {}C`\n' \
            '`Вечером: {}C — {}C`\n\n' \
            '{}'.format(status[0].strip(), *temp, status[1].strip())
    return daily


async def morning_msg():
    text = ''

    # TODO: добавить генерацию разных вариантов приветствий
    text += 'Доброе утро, народ!'
    # TODO: Проверять на наличие картинки
    text += ' [😺](https://t.me/funkcat/{})'.format(random.randint(1, 826))
    text += '\n'

    month_names = [u'января', u'февраля', u'марта',
                   u'апреля', u'мая', u'июня',
                   u'июля', u'августа', u'сентября',
                   u'октября', u'ноября', u'декабря']

    weekday_names = [u'понедельник', u'вторник', u'среда', u'четверг', u'пятница', u'суббота', u'воскресенье']

    now = datetime.datetime.now(pytz.timezone('Europe/Moscow'))

    people_in_chat = await my_bot.get_chat_members_count(config.mm_chat)
    print(people_in_chat)

    text += 'Сегодня *{} {}*, *{}*. Нас в чате *{}*!'.format(now.day, month_names[now.month - 1],
                                                             weekday_names[now.weekday()],
                                                             people_in_chat)
    text += '\n\n'
    text += '{}'.format(daily_weather())
    text += '\n\n'

    text += 'Котик дня:'

    # Отправить и запинить сообщение без уведомления
    msg = await my_bot.send_message(config.mm_chat, text, parse_mode="Markdown")
    await my_bot.pin_chat_message(config.mm_chat, msg.message_id, disable_notification=True)

    action_log('Scheduled morning message sent: id = {}'.format(msg.message_id))


async def unpin_msg():
    message = (await my_bot.get_chat(config.mm_chat)).pinned_message
    if message is not None:
        if message.from_user.is_bot is True:
            await my_bot.unpin_chat_message(config.mm_chat)


async def schedule_morning_messages():
    while True:
        now = datetime.datetime.now(pytz.timezone('Europe/Moscow'))

        if now.hour == 7 and now.minute == 0:
            await morning_msg()
            await asyncio.sleep(60)

        elif now.hour == 13 and now.minute == 0:
            await unpin_msg()
            await asyncio.sleep(60)

        await asyncio.sleep(10)
