import jinja2

from heimdallm.bifrosts.sql.envelope import PromptEnvelope as _SQLPromptEnvelope


class PromptEnvelope(_SQLPromptEnvelope):
    __doc__ = _SQLPromptEnvelope.__doc__

    def template(self, env: jinja2.Environment) -> jinja2.Template:
        """
        Returns the template to use for the envelope. Override in a subclass for
        complete customization.

        :param env: The environment to use to load the template.
        :return: The template to use for the envelope.
        """
        return env.get_template("sql/sqlite/select.j2")
