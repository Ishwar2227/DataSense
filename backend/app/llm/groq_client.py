import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError(
        "GROQ_API_KEY was not found. Check your backend/.env file."
    )

client = Groq(api_key=api_key)


def generate_answer(prompt: str) -> str:
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a business data analyst for DataSense. "
                    "Use ONLY the facts and numbers provided in the prompt. "
                    "Never invent causes, explanations, or data. "
                    "If the provided data does not explain why something happened, "
                    "say that the available data does not provide the reason. "
                    "Give a concise, professional business answer."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
        max_completion_tokens=300,
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError("Groq returned an empty response.")

    return content.strip()