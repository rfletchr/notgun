from __future__ import annotations
from pathlib import Path
import os
import glob
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from string import Formatter
import typing
from typing import Any, NamedTuple

_TEMPLATE_REF = re.compile(r"<([a-zA-Z_]\w*)>")

PathTemplateDict = dict[str, "PathTemplate"]


class FrameStyle(Enum):
    """Controls the placeholder style used by :meth:`Token.frame`."""

    HASH_1 = auto()  # one "#" per digit of padding  (e.g. "####" for padding=4)
    HASH_4 = auto()  # one "#" per four digits        (e.g. "#"  for padding=4)
    PRINTF = auto()  # C printf specifier             (e.g. "%04d" for padding=4)


class Placeholder(str):
    """A sentinel string value representing an unfilled token position.

    Inherits from str so it can be used anywhere a string is expected.
    Use isinstance(value, Placeholder) to detect placeholder values.
    """


@dataclass
class Token:
    """A named placeholder in a template string.

    Handles both formatting a value into a string and parsing a string back
    into its original type.

    Attributes:
        regex:       Pattern used to match this token's value during parsing.
        fmt:         Python format specifier (e.g. "03d", "s", ".2f").
        converter:   Callable that converts a matched string to its original type.
        placeholder: Optional literal string treated as a valid stand-in value
                     (e.g. "#" for frame numbers).  Bypasses regex matching.
    """

    regex: str
    fmt: str
    converter: Callable[[str], Any] = field(default=str)
    placeholder: typing.Union[Placeholder, None] = field(default=None)

    @classmethod
    def identifier(cls) -> "Token":
        """Token matching a mixed-case identifier (letters, digits, underscores,
        starting with a letter or digit)."""
        return cls(regex=r"[a-zA-Z0-9][a-zA-Z0-9_]*", fmt="s")

    @classmethod
    def integer(cls, padding: int = 0) -> "Token":
        """Token matching a whole number, with optional zero-padding width."""
        fmt = f"0{padding}d" if padding else "d"
        return cls(regex=r"\d+", fmt=fmt, converter=int)

    @classmethod
    def frame(cls, padding: int = 4, style: FrameStyle = FrameStyle.HASH_4) -> "Token":
        """Token matching a frame number with a style-specific placeholder.

        Args:
            padding: Number of digits to zero-pad to.
            style:   Controls the placeholder representation.

        Raises:
            ValueError: If *style* is ``HASH_4`` and *padding* is not divisible by 4.
        """
        if style == FrameStyle.HASH_1:
            placeholder = Placeholder("#" * padding)
        elif style == FrameStyle.HASH_4:
            if padding % 4 != 0:
                raise ValueError(
                    f"HASH_4 requires padding divisible by 4, got {padding}"
                )
            placeholder = Placeholder("#" * (padding // 4))
        elif style == FrameStyle.PRINTF:
            placeholder = Placeholder(f"%0{padding}d")
        return cls(
            regex=r"\d+", fmt=f"0{padding}d", converter=int, placeholder=placeholder
        )

    def format(self, value: Any) -> str:
        """Render *value* using this token's format specifier.

        If *value* equals this token's placeholder it is returned as-is.
        """
        if self.placeholder is not None and value == self.placeholder:
            return str(value)

        return format(value, self.fmt)

    def parse(self, s: str) -> Any:
        """Validate *s* against this token's regex and return the converted value.

        If *s* exactly matches this token's placeholder it is returned as a
        Placeholder instance without applying the regex or converter.

        Raises:
            ValueError: If *s* does not match the placeholder or the token's regex.
        """
        if self.placeholder is not None and s == self.placeholder:
            return Placeholder(s)
        if re.fullmatch(self.regex, s) is None:
            raise ValueError(f"Value {s!r} does not match token pattern {self.regex!r}")
        return self.converter(s)


class Template:
    """A string template that supports both formatting and parsing.

    Args:
        fmt:     Python format string using field names only, no specifiers
                 (e.g. "{seq}/{shot}/frame.{frame}.exr").
        pattern: Regex pattern for parsing, with named groups for the first
                 occurrence of each field and backreferences for repeats
                 (e.g. r"(?P<seq>\\w+)/(?P<shot>\\w+)/frame\\.(?P<frame>\\d+)\\.exr").
        tokens:  Mapping of field name to Token for each field used in the template.
    """

    def __init__(self, fmt: str, pattern: str, tokens: dict[str, Token]) -> None:
        self._fmt = fmt
        self._pattern = pattern
        self._tokens = tokens
        self._compiled = re.compile(pattern)

    @property
    def fmt(self) -> str:
        return self._fmt

    @property
    def pattern(self) -> str:
        return self._pattern

    @property
    def tokens(self) -> dict[str, Token]:
        return self._tokens

    def token_names(self) -> set[str]:
        return set(self._tokens.keys())

    def format(self, values: dict[str, Any]) -> str:
        """Render the template by applying each token's format spec to its value."""
        formatted = {
            name: self._tokens[name].format(value) for name, value in values.items()
        }
        return self._fmt.format_map(formatted)

    def parse(self, s: str) -> typing.Union[dict[str, Any], None]:
        """Extract and convert field values from *s* using the template pattern.

        Raises:
            ValueError: If *s* does not fully match the template pattern.
        """

        return self.fullmatch(s)

    def match(self, s: str) -> typing.Union[dict[str, Any], None]:
        m = self._compiled.match(s)
        if m is None:
            return None

        return {
            name: self._tokens[name].parse(value)
            for name, value in m.groupdict().items()
        }

    def fullmatch(self, s: str) -> typing.Union[dict[str, Any], None]:
        m = self._compiled.fullmatch(s)
        if m is None:
            return None

        return {
            name: self._tokens[name].parse(value)
            for name, value in m.groupdict().items()
        }


class PathTemplate(Template):
    """A Template that operates relative to a fixed root directory.

    Args:
        root:    Absolute path to the root directory.
        fmt:     See :class:`Template`.
        pattern: See :class:`Template`.
        tokens:  See :class:`Template`.
    """

    def __init__(
        self, root: str, fmt: str, pattern: str, tokens: dict[str, Token]
    ) -> None:
        self._root = root
        super().__init__(fmt, pattern, tokens)

    @property
    def root(self) -> str:
        return self._root

    def parse(self, s: str) -> typing.Union[dict[str, Any], None]:
        """Parse an absolute path, stripping the root before matching the template.

        Raises:
            ValueError: If *s* is not an absolute path.
            ValueError: If *s* does not share the template root.
        """
        return self.fullmatch(s)

    def match(self, s: str) -> typing.Union[dict[str, Any], None]:
        if not os.path.isabs(s):
            return None
        rel = os.path.relpath(s, self._root)
        if rel.startswith(".."):
            return None
        return super().match(rel)

    def fullmatch(self, s: str) -> typing.Union[dict[str, Any], None]:
        if not os.path.isabs(s):
            return None

        rel = os.path.relpath(s, self._root)
        if rel.startswith(".."):
            return None
        return super().fullmatch(rel)

    def glob(self, values: dict[str, Any]) -> list[str]:
        """Return a list of absolute paths matching the template with *values* applied as glob patterns."""

        formatted = {}
        for name, token in self._tokens.items():
            value = values.get(name)
            formatted[name] = token.format(value) if value else "*"

        rel_pattern = self._fmt.format_map(formatted)
        abs_pattern = os.path.join(self._root, rel_pattern)
        return glob.glob(abs_pattern)

    def format(self, values: dict[str, Any]) -> str:
        """Format values into a template string and join to the root."""
        return os.path.join(self._root, super().format(values))


def expand_templates(definitions: dict[str, str]) -> dict[str, str]:
    """Recursively expand template references in a dict of template definitions.

    References use the syntax ``<name>`` and are replaced inline with the
    corresponding definition.  Token placeholders (``{name}``) are left
    untouched.

    Args:
        definitions: Mapping of template name to template string.

    Returns:
        A new dict with all ``<name>`` references fully expanded.

    Raises:
        KeyError:   If a referenced name is not present in *definitions*.
        ValueError: If a circular reference is detected.
    """
    expanded: dict[str, str] = {}
    stack: list[str] = []

    def _expand(name: str) -> str:
        if name in expanded:
            return expanded[name]
        if name not in definitions:
            raise KeyError(f"Unknown template reference: {name!r}")
        if name in stack:
            cycle = " -> ".join((*stack[stack.index(name) :], name))
            raise ValueError(f"Circular template reference: {cycle}")

        stack.append(name)
        result = _TEMPLATE_REF.sub(lambda m: _expand(m.group(1)), definitions[name])
        stack.pop()
        expanded[name] = result
        return result

    for name in definitions:
        _expand(name)

    return expanded


class CompiledTemplate(NamedTuple):
    fmt: str
    pattern: str
    tokens: dict[str, Token]


def compile_template(definition: str, tokens: dict[str, Token]) -> CompiledTemplate:
    """Parse and validate a template definition, returning its components.

    Walks the definition string using :func:`string.Formatter.parse` to
    validate field references and build the regex pattern.

    Args:
        definition: Fully-expanded template string containing only ``{name}``
                    token placeholders and literal text.
        tokens:     Mapping of all available token names to their Token objects.

    Returns:
        A :class:`CompiledTemplate` with ``fmt``, ``pattern``, and the subset
        of *tokens* actually referenced by the definition.

    Raises:
        KeyError:   If a field name is not found in *tokens*.
        ValueError: If the definition contains unresolved ``<ref>`` references,
                    format specifiers, or two adjacent token fields with no
                    literal separator between them.
    """
    if _TEMPLATE_REF.search(definition):
        raise ValueError(
            f"Definition contains unresolved template references: {definition!r}"
        )

    pattern_parts: list[str] = []
    used_tokens: dict[str, Token] = {}
    seen: set[str] = set()
    prev_was_field = False

    for literal, field_name, fmt_spec, _ in Formatter().parse(definition):
        pattern_parts.append(re.escape(literal))

        if field_name is None:
            prev_was_field = False
            continue

        if fmt_spec:
            raise ValueError(
                f"Field {field_name!r} contains a format specifier {fmt_spec!r}; "
                "specifiers belong on the Token, not the definition."
            )
        if field_name not in tokens:
            raise KeyError(f"Unknown token: {field_name!r}")
        if prev_was_field and not literal:
            raise ValueError(
                f"Token {field_name!r} is directly adjacent to the preceding token "
                "with no literal separator, which would make parsing ambiguous."
            )

        if field_name in seen:
            pattern_parts.append(f"(?P={field_name})")
        else:
            pattern_parts.append(f"(?P<{field_name}>{tokens[field_name].regex})")
            seen.add(field_name)
            used_tokens[field_name] = tokens[field_name]

        prev_was_field = True

    return CompiledTemplate(
        fmt=definition,
        pattern="".join(pattern_parts),
        tokens=used_tokens,
    )


def compile_path_templates(
    projects_root: str, template_defs: dict[str, str], tokens: dict[str, Token]
) -> dict[str, PathTemplate]:
    expanded_defs = expand_templates(template_defs)

    path_templates = dict[str, PathTemplate]()

    for template_name, template_str in expanded_defs.items():
        compiled = compile_template(template_str, tokens)
        path_templates[template_name] = PathTemplate(
            projects_root,
            compiled.fmt,
            compiled.pattern,
            compiled.tokens,
        )

    return path_templates
