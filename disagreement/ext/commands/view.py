# disagreement/ext/commands/view.py

import re


class StringView:
    """
    A utility class to help with parsing strings, particularly for command arguments.
    It keeps track of the current position in the string and provides methods
    to read parts of it.
    """

    def __init__(self, buffer: str):
        self.buffer: str = buffer
        self.original: str = buffer  # Keep original for error reporting if needed
        self.index: int = 0
        self.end: int = len(buffer)
        self.previous: int = 0  # Index before the last successful read

    @property
    def remaining(self) -> str:
        """Returns the rest of the string that hasn't been consumed."""
        return self.buffer[self.index :]

    @property
    def eof(self) -> bool:
        """Checks if the end of the string has been reached."""
        return self.index >= self.end

    def skip_whitespace(self) -> None:
        """Skips any leading whitespace from the current position."""
        while not self.eof and self.buffer[self.index].isspace():
            self.index += 1

    def get_word(self) -> str:
        """
        Reads a "word" from the current position.
        A word is a sequence of non-whitespace characters.
        """
        self.skip_whitespace()
        if self.eof:
            return ""

        self.previous = self.index
        match = re.match(r"\S+", self.buffer[self.index :])
        if match:
            word = match.group(0)
            self.index += len(word)
            return word
        return ""  # Should not happen if not eof and skip_whitespace was called

    def get_quoted_string(self) -> str:
        """
        Reads a string enclosed in double quotes.
        Handles escaped quotes inside the string.
        """
        self.skip_whitespace()
        if self.eof or self.buffer[self.index] != '"':
            return ""  # Or raise an error, or return None

        self.previous = self.index
        self.index += 1  # Skip the opening quote
        result = []
        escaped = False

        while not self.eof:
            char = self.buffer[self.index]
            self.index += 1

            if escaped:
                result.append(char)
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                return "".join(result)  # Closing quote found
            else:
                result.append(char)

        # If loop finishes, means EOF was reached before closing quote
        # This is an error condition. Restore index and indicate failure.
        self.index = self.previous
        # Consider raising an error like UnterminatedQuotedStringError
        return ""  # Or raise

    def read_rest(self) -> str:
        """Reads all remaining characters from the current position."""
        self.skip_whitespace()
        if self.eof:
            return ""

        self.previous = self.index
        result = self.buffer[self.index :]
        self.index = self.end
        return result

    def undo(self) -> None:
        """Resets the current position to before the last successful read."""
        self.index = self.previous

    # Could add more methods like:
    # peek() - look at next char without consuming
    # match_regex(pattern) - consume if regex matches
