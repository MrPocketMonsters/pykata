"""A total cost calculator with tax applied."""


def calculate_total_cost(costs: dict, items: list, tax: float) -> float:
    """
    Calculate the total cost of items including tax.

    Args:
        costs (dict): A dictionary with item names as keys and their costs as values.
        items (list): A list of items bought.
        tax (float): The tax rate to be applied. E.g., 0.10 for 10% tax.

    Returns:
        float: The total cost rounded to two decimal places.
    """
    total = 0.0
    for item in items:
        if item in costs:
            total += costs[item]
    total_with_tax = total * (1 + tax)
    return round(total_with_tax, 2)


if __name__ == "__main__":
    # First input: dictionary of costs
    costs = eval(input())
    if type(costs) is not dict:
        raise ValueError("First input must be a dictionary.")

    # Second input: list of items bought
    items = eval(input())
    if type(items) is not list:
        raise ValueError("Second input must be a list.")

    # Third input: tax rate
    tax = float(input())

    result = calculate_total_cost(costs, items, tax)
    print(result)
