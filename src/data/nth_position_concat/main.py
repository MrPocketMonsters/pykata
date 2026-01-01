"""A function to concatenate the nth character from each string in an array."""


def nth_position_concat(strings: list) -> str:
    """
    Concatenate the nth character from each string in the array,
    where n is the index of the string in the array.

    If a string is shorter than n+1 characters, it is skipped.

    Args:
        strings (list): A list of strings.

    Returns:
        str: The concatenated string.
    """
    result = []
    for index, string in enumerate(strings):
        if len(string) > index:
            result.append(string[index])
    return "".join(result)


if __name__ == "__main__":
    # Input: list of strings
    strings = eval(input())
    if type(strings) is not list:
        raise ValueError("Input must be a list.")

    for s in strings:
        if type(s) is not str:
            raise ValueError("All elements in the list must be strings.")

    result = nth_position_concat(strings)
    print(result)
