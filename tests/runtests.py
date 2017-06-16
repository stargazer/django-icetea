#!/usr/bin/env python
import os
import sys

from django.core.management import execute_from_command_line

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sample.settings")


def main():
    try:
        import django
        django.setup()
    except AttributeError:
        pass

    args = [sys.argv[0], 'test']
    # Current module (``tests``) and its submodules.
    test_cases = '.'

    # Allow accessing test options from the command line.
    offset = 1
    try:
        sys.argv[1]
    except IndexError:
        pass
    else:
        option = sys.argv[1].startswith('-')
        if not option:
            test_cases = sys.argv[1]
            offset = 2

    args.append(test_cases)
    # ``verbosity`` can be overwritten from command line.
    args.append('--verbosity=2')
    args.extend(sys.argv[offset:])

    execute_from_command_line(args)


if __name__ == "__main__":
    main()
