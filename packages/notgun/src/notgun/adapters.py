import abc


class ApplicationAdapter(abc.ABC):
    @abc.abstractmethod
    def filepath(self) -> str | None: ...

    @abc.abstractmethod
    def is_dirty(self) -> bool: ...

    @abc.abstractmethod
    def save(self): ...

    @abc.abstractmethod
    def save_as(self, filepath: str): ...
