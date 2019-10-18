# usr/bin/env python3

from cli import CommandLineInterface


if __name__ == '__main__':
    try:
        cli = CommandLineInterface()
        cli.run()
    except KeyboardInterrupt:
        exit(0)
