from typing import Callable


def menu(prompt: str, options: list, validator: Callable[[str], bool]):
    print(prompt)
    for opt in options:
        print(opt)
    response = input("> ")
    while not validator(response):
        input("> ")
    return response


def ask(prompt: str, validation: Callable[[str], bool]):
    print(prompt)
    response = input("> ")
    while not validation(response):
        input("> ")
    return response


def yn_question(prompt: str):
    print(prompt + " (y/n)")
    response = input("> ")
    while not any(response.lower().startswith(s) for s in 'yn'):
        input("> ")
    return response.startswith('y')
