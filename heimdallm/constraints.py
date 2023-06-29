from abc import ABC, abstractmethod

from lark import Lark, ParseTree


class ConstraintValidator(ABC):
    @abstractmethod
    def fix(self, Grammar: Lark, tree: ParseTree) -> str:
        """if the tree does not pass the constraints, attempt to reconstruct it
        to satisfy the constraints. if the tree cannot be reconstructed, throw a
        bifrost-specific exception"""
        pass

    @abstractmethod
    def validate(self, untrusted_input: str, tree: ParseTree):
        """throws a bifrost-specific exception if the tree does not pass the
        constraints. the untrusted_input is provided for context if we need to raise
        an exception that contains the original input."""
        pass
