from collections import namedtuple

import colorama


__all__ = ["RunContext", "CharacterOccurrence"]

CharacterOccurrence = namedtuple("CharacterOccurrence", ["pos", "char"])


class RunContext(namedtuple("RunContext", ["chapter", "prev", "run", "next"])):
    def highlight(self, i, w):
        prev = colorama.Fore.LIGHTBLACK_EX + "\n".join(self.prev) + colorama.Fore.RESET
        next = colorama.Fore.LIGHTBLACK_EX + "\n".join(self.next) + colorama.Fore.RESET

        run = " ".join(
            tkn
            for sublist in [
                self.run[:i],
                [colorama.Style.BRIGHT],
                self.run[i : i + w],
                [colorama.Style.NORMAL],
                self.run[i + w :],
            ]
            for tkn in sublist
        )

        return RunContext(chapter=self.chapter, prev=prev, run=run, next=next)
