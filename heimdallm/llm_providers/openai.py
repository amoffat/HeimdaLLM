import openai

from heimdallm import llm


class Client(llm.LLMIntegration):
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo-16k"):
        self.api_key = api_key
        self.model = model

    def complete(self, untrusted_user_input: str) -> str:
        chat_completion = openai.ChatCompletion.create(
            api_key=self.api_key,
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": untrusted_user_input,
                }
            ],
        )
        untrusted_llm_output = chat_completion.choices[0].message.content
        return untrusted_llm_output


# def generate_text(prompt, model="text-davinci-003", max_tokens=256):
#     response = openai.Completion.create(
#         engine=model,
#         prompt=prompt,
#         max_tokens=max_tokens,
#         n=1,
#         stop=None,
#         temperature=0.7,
#     )
#     return response.choices[0].text.strip()
