import abc


class NotSavedError(Exception): ...


class ApplicationAdapter(abc.ABC):
    @abc.abstractmethod
    def filepath(self) -> str | None: ...

    @abc.abstractmethod
    def modified(self) -> bool: ...

    @abc.abstractmethod
    def save(self): ...

    @abc.abstractmethod
    def save_as(self, filepath: str): ...

    @abc.abstractmethod
    def open(self, filepath: str): ...

    @abc.abstractmethod
    def new(self): ...
