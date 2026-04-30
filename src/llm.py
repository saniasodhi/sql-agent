import os
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the client once. The SDK reads ANTHROPIC_API_KEY from the env automatically.
client = Anthropic()


def ask_claude(
    question: str,
    system_prompt: str = "You are a helpful, concise assistant.",
    model: str = "claude-haiku-4-5-20251001",
) -> str:
    """
    Send a question to Claude and return its text response.

    Args:
        question: The user's question.
        system_prompt: Instructions that shape Claude's behavior (role, tone, constraints).
        model: Which Claude model to use.

    Returns:
        Claude's response as a plain string.
    """
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=system_prompt,
        messages=[
            {"role": "user", "content": question}
        ],
    )
    return response.content[0].text


# if __name__ == "__main__":
#     question = "What is SQL?"

#     # Default system prompt
#     print("--- Default ---")
#     print(ask_claude(question))
#     print()

#     # As a SQL teacher to a beginner
#     print("--- As a teacher to a 10-year-old ---")
#     print(ask_claude(
#         question,
#         system_prompt="You are a patient teacher explaining concepts to a 10-year-old. Use simple words and an analogy."
#     ))
#     print()

#     # Terse expert
#     print("--- As a terse expert ---")
#     print(ask_claude(
#         question,
#         system_prompt="You are a senior database engineer. Answer in one sentence, no fluff."
#     ))

if __name__ == "__main__":
    question = "What is SQL?"

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": question}],
    )

    print("Response:", response.content[0].text)
    print()
    print("Input tokens:", response.usage.input_tokens)
    print("Output tokens:", response.usage.output_tokens)