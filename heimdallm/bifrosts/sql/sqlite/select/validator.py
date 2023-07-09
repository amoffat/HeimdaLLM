from heimdallm.bifrosts.sql.validator import (
    ConstraintValidator as _SQLConstraintValidator,
)

from .. import presets


class ConstraintValidator(_SQLConstraintValidator):
    __doc__ = _SQLConstraintValidator.__doc__

    def can_use_function(self, function: str) -> bool:
        """
        Returns whether or not a SQL function is allowed to be used anywhere in the
        query. By default, this checks the function against the list of safe functions
        that we have curated by hand.

        :param function: The *lowercase* name of the function.
        :return: Whether or not the function is allowed.
        """
        return function in presets.safe_functions
