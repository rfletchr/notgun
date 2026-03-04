import notgun
import dataclasses
import notgun.templates

__TEST_TOKEN = notgun.templates.Token.identifier()


@dataclasses.dataclass(frozen=True)
class Context:
    project: str
    epsiode: str | None = None
    sequence: str | None = None
    shot: str | None = None
    task: str | None = None
    asset_type: str | None = None
    asset: str | None = None

    def __post_init__(self):
        if self.task and not (self.shot or self.asset):
            raise ValueError("task cannot be set without a shot or asset.")

        if self.asset_type and (self.sequence or self.epsiode):
            raise ValueError(
                "asset type and sequence/episode cannot be set at the same time."
            )

        if self.asset and self.sequence:
            raise ValueError("asset and sequence cannot be set at the same time.")

        if self.asset and not self.asset_type:
            raise ValueError("asset cannot be set without asset type.")

        if self.shot and not self.sequence:
            raise ValueError("shot cannot be set without sequence.")

        for field in dataclasses.fields(Context):
            value = getattr(self, field.name)

            if value is None:
                continue

            if value == "":
                raise ValueError(f"value of {field.name} cannot be an empty string")

            try:
                __TEST_TOKEN.parse(value)
            except ValueError:
                raise ValueError(f"{field.name} contains invalid value: {value}")

    def as_dict(self) -> dict[str, str]:
        result = dict[str, str]()
        for field in dataclasses.fields(self):
            value = getattr(self, field.name)
            if value is None:
                continue

            result[field.name] = value

        return result
