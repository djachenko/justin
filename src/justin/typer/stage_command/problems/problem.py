from dataclasses import dataclass


@dataclass(frozen=True)
class Problem:
    """Базовый класс проблемы. Текст — в наследниках."""

    def __str__(self) -> str:
        raise NotImplementedError
