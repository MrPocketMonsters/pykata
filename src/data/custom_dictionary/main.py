# Exceptions
"""A custom dictionary implementation with exception handling for key management."""


class CustomDictionaryKeyAlreadyExistsError(Exception):
    """Raised when trying to add a key that already exists in the dictionary."""


class CustomDictionaryKeyNotFoundError(Exception):
    """Raised when trying to access or remove a key that does not exist in the dictionary."""


class CustomDictionaryEntry:
    """Represents a single entry in the custom dictionary."""

    def __init__(self, key: str, value: str) -> None:
        """Creates a new custom dictionary entry.

        Args:
            key (str): The key of the entry.
            value (str): The value associated with the key.
        """
        self.key = key
        self.value = value

    def __repr__(self) -> str:
        return f'"{self.key}":"{self.value}"'


class CustomDictionary:
    """A custom dictionary that manages key-value pairs with specific constraints."""

    def __init__(self) -> None:
        self.__entries: list[CustomDictionaryEntry] = []

    def __find(self, key: str) -> CustomDictionaryEntry:
        """Finds an entry by key."""
        return next((entry for entry in self.__entries if entry.key == key), None)

    def add(self, key: str, value: str) -> None:
        """Adds a new entry to the dictionary.

        Args:
            key (str): The key of the entry.
            value (str): The value associated with the key.

        Raises:
            CustomDictionaryKeyAlreadyExistsError: If the key already exists.
        """
        entry = self.__find(key)
        if entry is not None:
            raise CustomDictionaryKeyAlreadyExistsError(f'Key "{key}" already exists.')
        self.__entries.append(CustomDictionaryEntry(key, value))

    def remove(self, key: str) -> None:
        """Removes an entry by key.

        Args:
            key (str): The key of the entry to remove.

        Raises:
            CustomDictionaryKeyNotFoundError: If the key does not exist.
        """
        entry = self.__find(key)
        if entry is None:
            raise CustomDictionaryKeyNotFoundError(f'Key "{key}" not found.')
        self.__entries.remove(entry)

    def set(self, key: str, value: str) -> None:
        """Sets the value of an existing entry.

        Args:
            key (str): The key of the entry.
            value (str): The new value to set.

        Raises:
            CustomDictionaryKeyNotFoundError: If the key does not exist.
        """
        entry = self.__find(key)
        if entry is None:
            raise CustomDictionaryKeyNotFoundError(f'Key "{key}" not found.')
        entry.value = value

    def get(self, key: str) -> str:
        """Retrieves an entry by key.

        Args:
            key (str): The key of the entry to retrieve.

        Raises:
            CustomDictionaryKeyNotFoundError: If the key does not exist.
        """
        entry = self.__find(key)
        if entry is None:
            raise CustomDictionaryKeyNotFoundError(f'Key "{key}" not found.')
        return entry.value

    def __repr__(self) -> str:
        entries_repr = ", ".join(repr(entry) for entry in self.__entries)
        return f"{{{entries_repr}}}"


if __name__ == "__main__":
    # Create instance and define actions
    custom_dict = CustomDictionary()
    actions = {"ADD", "REMOVE", "SET", "GET"}

    # Get the next line. If it's "END", stop the program
    while (line := input()) != "END":

        # Extract action from parsed command
        command = line.split()
        action = command[0]

        if action not in actions:
            print("[ERROR - INVALID COMMAND]")
            continue

        # If theres only one element, it's an error
        if len(command) < 2:
            print("[ERROR - NO KEY]")
            continue

        # Extract the key and perform the action ready for exceptions
        key = command[1]
        try:

            if action == "ADD":
                custom_dict.add(key, None)
                print("[CREATED]")

            elif action == "REMOVE":
                custom_dict.remove(key)
                print("[REMOVED]")

            elif action == "SET":
                try:
                    # Extract the value
                    value = command[2]
                    custom_dict.set(key, value)
                    print(f"[SET TO {value}]")
                # If there's no third element, it's an error
                except IndexError:
                    print("[ERROR - NO VALUE]")

            elif action == "GET":
                print(custom_dict.get(key))

        # Handle exceptions
        except CustomDictionaryKeyAlreadyExistsError:
            print("[ERROR - ALREADY EXISTS]")
        except CustomDictionaryKeyNotFoundError:
            print("[ERROR - NOT FOUND]")
