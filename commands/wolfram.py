#!/usr/bin/env python3
import io

import requests
from PIL import Image

import tokens
from utils import user_action_log


async def wolfram_solver(message):
    """
    обрабатывает запрос и посылает пользователю картинку с результатом в случае удачи
    :param message:
    :return:
    """
    # сканируем и передаём всё, что ввёл пользователь после '/wolfram ' или '/wf '
    if not len(message.text.split()) == 1:
        # my_bot.send_chat_action(message.chat.id, 'upload_photo')
        your_query = ' '.join(message.text.split()[1:])
        user_action_log(message, "entered this query for /wolfram:\n{0}".format(your_query))
        response = requests.get("https://api.wolframalpha.com/v1/simple?appid=" + tokens.wolfram,
                                params={'i': your_query})
        # если всё хорошо, и запрос найден
        if response.status_code == 200:
            img_original = Image.open(io.BytesIO(response.content))
            img_cropped = img_original.crop((0, 95, 540, img_original.size[1] - 50))
            io_img = io.BytesIO()
            io_img.name = "wolfram {}.png".format(your_query.replace("/", "_"))
            img_cropped.save(io_img, format="png")
            io_img.seek(0)
            wolfram_max_ratio = 2.5
            if img_cropped.size[1] / img_cropped.size[0] > wolfram_max_ratio:
                await message.reply_document(io_img)
            else:
                await message.reply_photo(io_img)
            user_action_log(message, "has received this Wolfram output:\n{0}".format(response.url))
        # если всё плохо
        else:
            await message.reply("Запрос не найдён.\nЕсли ты ввёл его на русском, "
                            "то попробуй ввести его на английском.")
            user_action_log(message, "didn't received any data")
    # если пользователь вызвал /wolfram без аргумента
    else:
        await message.reply("Использование: `/wolfram <запрос>` или `/wf <запрос>`", parse_mode="Markdown")
        user_action_log(message, "called /wolfram without any arguments")