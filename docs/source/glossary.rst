🔍 Glossary
===========

.. glossary::

    autofixing
        An alias for :term:`reconstruction`.

    :doc:`Bifrost </bifrost>`
        An object that can traverse untrusted human input into untrusted
        machine-readable input.

    :doc:`constraint validator </api/abc/validator>`
        An object that is capable of analyzing an LLM's structured output to determine
        if the output is compliant with a set of constraints.

    externalizing
        The process of making a technology, service, or system available to untrusted
        external users.

    grammar
        A set of rules that define the actual structure of an LLM's structured output.
        The grammar is used by a parser to turn some text into a structured tree.

    LLM
        A Large Language Model. A machine learning model that can produce desired text
        from some prompt. e.g. `ChatGPT <https://openai.com/blog/chatgpt>`_

    prompt envelope
        Extra context wrapped around untrusted input to guide an LLM into producing
        desired output.

    prompt injection
        A technique for exploiting an LLM by crafting a prompt that causes the LLM to
        produce output that is considered harmful.

    :doc:`reconstruction </reconstruction>`
        The process of rebuilding LLM's structured output to be compliant with a
        constraint validator.

    traveral
        Translating input with a Bifrost.