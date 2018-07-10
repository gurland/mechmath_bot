#!/usr/bin/env python3
import re
from io import BytesIO
from datetime import datetime
from html.parser import HTMLParser
import logging

import asyncio
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from PIL import Image, ImageFont, ImageDraw

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


def create_collage(images, tile_height=160, tile_width=240, tile_offset=0, cols=5, gap=2, padding=5,
                   resize=True, font_size=20, font_color='#000', font_padding=10, bgcolor='#fff', write=True):
    # Create canvas.
    tile_count = len(images) + tile_offset
    rows = tile_count // cols + (1 if tile_count % cols else 0)
    imgsize = (2 * padding + tile_height * cols +
               gap * (cols - 1),
               2 * padding + tile_width * rows +
               gap * (rows - 1))
    img = Image.new('RGB', imgsize, bgcolor)

    imgno = 0

    for tile_file, db_id in images:
        # Tile position.
        pos = imgno + tile_offset
        x = pos % cols
        y = pos // cols
        # Offsets.
        xoff = padding + x * (tile_height + gap)
        yoff = padding + y * (tile_width + gap)

        tile = Image.open(BytesIO(tile_file))

        # resize image if necessary!
        if resize and tile.size != (tile_height, tile_width) and all(tile.size):
            w_from, h_from = tile.size
            if (w_from / float(h_from) >
                    tile_height / float(tile_width)):
                w_to = tile_height
                h_to = int(w_to / float(w_from) * h_from)
            else:
                h_to = tile_width
                w_to = int(h_to / float(h_from) * w_from)

            try:
                tile = tile.resize((w_to, h_to), Image.ANTIALIAS)
            except ValueError:
                error_log('Could not resize sticker')

        # Place tile on canvas.
        img.paste(tile, (xoff, yoff))

        # Write a number on the image, if desired.
        if write:
            font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSans.ttf", font_size)

            draw = ImageDraw.Draw(img)
            txt = f'{imgno+1} [{db_id}]'

            # Calculate offsets.
            txtsize = draw.textsize(txt, font=font)
            font_xoff = (xoff + tile_height - txtsize[0] -
                         font_padding)
            font_yoff = (yoff + tile_width - txtsize[1] -
                         font_padding)

            # Finally, draw the number.
            draw.text((font_xoff, font_yoff), txt, font=font,
                      fill=font_color)
            del draw

        imgno += 1

    result = BytesIO()
    img.save(result, format='JPEG')
    return result.getvalue()
