from unittest.mock import patch

from munch import munchify  # type: ignore

from heimdallm.llm_providers.openai import Client, OpenAIMethod


def test_chat_complete():
    with patch("heimdallm.llm_providers.openai.openai") as openai:
        openai.ChatCompletion.create.return_value = munchify(
            {"choices": [{"message": {"content": "world"}}]}
        )
        client = Client(api_key="secret", method=OpenAIMethod.CHAT)
        resp = client.complete("hello")
    assert resp == "world"


def test_completion_complete():
    with patch("heimdallm.llm_providers.openai.openai") as openai:
        openai.Completion.create.return_value = munchify(
            {"choices": [{"text": "world"}]}
        )
        client = Client(api_key="secret", method=OpenAIMethod.COMPLETION)
        resp = client.complete("hello")
    assert resp == "world"
