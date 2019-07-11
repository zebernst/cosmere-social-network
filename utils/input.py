from typing import Callable


def menu(prompt: str, options: list, validator: Callable[[str], bool], error: str = None):
    if prompt:
        print(prompt)
    for opt in options:
        print(opt)
    response = input("> ")
    while not validator(response):
        if error:
            print(error)
        response = input("> ")
    return response


def ask(prompt: str, validator: Callable[[str], bool], error: str = None):
    if prompt:
        print(prompt + " ('#' to cancel)")
    response = input("> ")
    while not (validator(response) or response == '#'):
        if error:
            print(error)
        response = input("> ")
    return response if response != '#' else None


def yn_question(prompt: str):
    print(prompt + " (y/n)")
    response = input("> ")
    while not any(response.lower().startswith(s) for s in 'yn'):
        response = input("> ")
    return response.startswith('y')
