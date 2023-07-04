🛡️ Attack Surface
=================

LLMs are vulnerable to :term:`prompt injection` attacks, which can be used to construct
responses that are dangerous to the system. This is the primary reason that LLMs have
not seen widespread adoption as :term:`externalized <externalizing>` products.

Prompt injection can have different consequences within different contexts, and this
page will reflect how different :doc:`Bifrosts </bifrost>` manage the attack surface
area.

.. toctree::
    :glob:

    attack_surface/*