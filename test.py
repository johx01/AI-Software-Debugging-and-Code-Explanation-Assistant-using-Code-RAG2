def calculate_total(price, quantity):
    total = price * quantity
    return total


def greet_user(name):
    message = f"Hello, {name}!"
    return message


def calculate_discount(price, discount):
    final_price = price - (price * discount / 100)
    return final_price