from app.llm.groq_client import generate_answer


prompt = """
Trusted DataSense statistics:

Previous month: November 2017
Previous value: 89306.24

Latest month: December 2017
Latest value: 56969.1958

Change: -32337.0442
Change percentage: -36.21%

Question:
Why did the value change?

Important:
The provided statistics show the amount and direction of the change,
but they do not provide the reason for the change.
Do not invent a reason.
"""


answer = generate_answer(prompt)

print("DATASENSE ANSWER:")
print(answer)