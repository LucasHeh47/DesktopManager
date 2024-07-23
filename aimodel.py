import asyncio
import time
import requests
from openai import OpenAI
import tts

client = OpenAI(base_url="http://localhost:42069/v1", api_key="lm-studio")

async def main(question):
    stream = client.chat.completions.create(
        model="TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
        messages=[
            {"role": "system", "content": "You are a computer assistant, please assist with any computer issues the client may have."},
            {"role": "user", "content": question}
        ],
        temperature=0.7,
        max_tokens=256,
        stream=True
    )

    last = time.time()
    textstream = ""

    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            text = chunk.choices[0].delta.content
            print(text, end="")
            textstream += text

        if time.time() > last + 1 and textstream:
            await tts.speak(textstream)
            last = time.time()
            textstream = ""

    # Ensure any remaining text is spoken
    if textstream:
        await tts.speak(textstream)

if __name__ == "__main__":
    asyncio.run(main(input("You: ")))
