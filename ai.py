from aiogram.enums import ChatAction
from google import genai
from google.genai.errors import ServerError
from google.genai.types import GenerateContentResponse
from lxml import html, etree
from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import CommandStart

from config import API_KEY, PROMPT

client = genai.Client(api_key=API_KEY)
router = Router()


def send_response(text: str) -> GenerateContentResponse | None:
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=PROMPT + text
        )
    except ServerError as e:
        response = send_response(text) if e.code == 503 else None
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
    response = send_response(message.html_text)
    text = response.text if response else 'Ошибка'
    if len(text) > 4096:
        paragraphs = text.split('\n\n')
        temp = ''
        texts = []
        for p in paragraphs:
            if len(temp + '\n\n' + p) > 4096:
                texts.append(correct_html(temp))
                temp = p
            else:
                temp += '\n\n' + p
        await mess.edit_text(texts[0], parse_mode='HTML')
        for text in texts[1:]:
            await message.answer(text, parse_mode='HTML')
    else:
        await mess.edit_text(text, parse_mode='HTML')

