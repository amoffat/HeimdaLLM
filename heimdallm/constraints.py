from abc import ABC, abstractmethod

from lark import Lark, ParseTree


class ConstraintValidator(ABC):
    @abstractmethod
    def fix(self, Grammar: Lark, tree: ParseTree) -> str:
        """If the tree fails validation in a soft-pass, attempt to reconstruct it
        to satisfy the constraints. If the tree cannot be reconstructed, throw a
        bifrost-specific exception

        :param Grammar: The Lark grammar used to parse the untrusted input. This is
            often used by :class:`lark.reconstruct.Reconstructor` to fix the parse tree.
        :param tree: The resulting parse tree of the untrusted input.
        """
        raise NotImplementedError

    @abstractmethod
    def validate(self, untrusted_input: str, tree: ParseTree):
        """This performs the Bifrost-specific validation of the parse tree. It throws a
        Bifrost-specific exception if the tree does not pass the constraints.

        :param untrusted_input: The untrusted input, which can be used to provide extra
            context if we need to raise an exception.
        :param tree: The resulting parse tree of the untrusted input.
        """
        raise NotImplementedError
