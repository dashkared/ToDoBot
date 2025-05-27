from openai import AsyncOpenAI, AsyncClient
from chatgpt_md_converter import telegram_format
import os
from dotenv import load_dotenv
from md2tgmd import escape
load_dotenv()

client = AsyncClient(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv('OPENAI_API'),
)

async def ai_generate(messages: list):
    completion = await client.chat.completions.create(
        model="deepseek/deepseek-chat-v3-0324:free",
        messages=messages
    )
    print(completion)
    return completion.choices[0].message.content