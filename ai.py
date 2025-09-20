from datetime import datetime

from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramBadRequest
from google import genai
from google.genai.errors import ServerError
from google.genai.types import GenerateContentResponse
from lxml import html
from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import CommandStart

from config import API_KEY, PROMPT
from db import execute_query

client = genai.Client(api_key=API_KEY)
router = Router()


def send_response(contents: list) -> GenerateContentResponse | None:
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents
        )
    except ServerError as e:
        print('чета ошибка какая-то')
        response = send_response(contents) if e.code == 503 else None
    return response


def replace_tags(string: str, *substrings: str):
    for substr in substrings:
        string = string.replace(f'<{substr}>', '').replace(f'</{substr}>', '')
    return string


def correct_html(text: str) -> str:
    tree = html.fromstring(f'<div>{text}</div>')
    corrected_html = html.tostring(tree, encoding='unicode')
    corrected_html = replace_tags(corrected_html, 'div', 'p', 'h3')
    return corrected_html


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer('старт')


@router.message()
async def answer_message(message: Message, bot: Bot):
    mess = await message.answer('⏳ Думаю...')
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    execute_query('insert into history values (?, ?, ?, ?)', message.from_user.id, 'user', message.html_text,
                  datetime.now().timestamp())
    contents = execute_query('select * from history where user_id = ? order by timestamp', message.from_user.id)
    dialogue_history = []
    for content in contents:
        dialogue_history.append({'role': content['sender'], 'parts': [{"text": content['content']}]})
    current_query = dialogue_history[-1]['parts']
    current_query[0]['text'] = PROMPT + current_query[0]['text']
    response = send_response(dialogue_history)
    text = response.text if response else 'Ошибка'
    execute_query('insert into history values (?, ?, ?, ?)', message.from_user.id, 'model', text,
                  datetime.now().timestamp())
    if len(text) > 4096:
        sep = '\n\n'
        paragraphs = text.split(sep)
        temp = ''
        texts = []
        for p in paragraphs:
            if p.find('<code>') != -1 and p.find('<code>') > p.find('</code>'):
                p = '<code>' + p
            if len(temp + sep + p) > 4090:
                texts.append(correct_html(temp))
                temp = p
            else:
                temp += sep + p
        texts = [text for text in texts if text]
        try:
            if not texts:
                texts.append('Ошибка!')
            await mess.edit_text(texts[0], parse_mode='HTML')
            for text in texts[1:]:
                await message.answer(text, parse_mode='HTML')
        except TelegramBadRequest as e:
            print(texts)
            print(e)
            pass
    else:
        await mess.edit_text(correct_html(text), parse_mode='HTML')

