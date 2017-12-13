#!/usr/bin/env python
import argparse
from prompt_toolkit import prompt
from prompt_toolkit.token import Token

from parser import KarelParser

def continuation_tokens(cli, width):
    return [(Token, ' ' * (width - 5) + '.' * 3 + ':')]

def is_multi_line(line):
    return line.strip()

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--world', type=str, default=None, help='Path to world text file')
    arg_parser.add_argument('--world_height', type=int, default=8, help='Height of square grid world')
    arg_parser.add_argument('--world_width', type=int, default=8, help='Width of square grid world')
    args = arg_parser.parse_args()

    line_no = 1
    parser = KarelParser()

    print('Press [Meta+Enter] or [Esc] followed by [Enter] to accept input.')
    while True:
        code = prompt(u'In [{}]: '.format(line_no), multiline=True,
                      get_continuation_tokens=continuation_tokens)

        if args.world is not None:
            parser.new_game(world_path=args.world)
        else:
            parser.new_game(world_size=(args.world_width, args.world_height))

        parser.draw("Input:  ")
        parser.run(code, debug=False)
        parser.draw("Output: ")
        line_no += 1
