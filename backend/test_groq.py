import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError(
        "GROQ_API_KEY was not found. "
        "Check your backend/.env file."
    )


client = Groq(
    api_key=api_key
)


response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {
            "role": "system",
            "content": (
                "You are a concise business data analyst. "
                "Answer clearly and briefly."
            )
        },
        {
            "role": "user",
            "content": (
                "Sales decreased by 36.2% from November to December. "
                "Explain this fact in one short business sentence. "
                "Do not invent a reason that is not provided."
            )
        }
    ],
    temperature=0.2,
    max_completion_tokens=300
)


print(response.choices[0].message.content)