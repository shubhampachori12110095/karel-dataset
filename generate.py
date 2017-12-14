#!/usr/bin/env python
import os
import argparse
import numpy as np
from tqdm import trange

from parser import KarelParser
from utils import str2bool, makedirs, TimeoutError, pprint, beautify, str2bool

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--train_num', type=int, default=1000000)
    arg_parser.add_argument('--test_num', type=int, default=5000)
    arg_parser.add_argument('--val_num', type=int, default=5000)
    arg_parser.add_argument('--data_dir', type=str, default='data')
    arg_parser.add_argument('--max_depth', type=int, default=5)
    arg_parser.add_argument('--mode', type=str, default='all')
    arg_parser.add_argument('--beautify', type=str2bool, default=False)
    arg_parser.add_argument('--world_height', type=int, default=8, help='Height of square grid world')
    arg_parser.add_argument('--world_width', type=int, default=8, help='Width of square grid world')
    args = arg_parser.parse_args()

    # Make directories
    makedirs(args.data_dir)
    datasets = ['train', 'test', 'val']

    # Generate datasets
    parser = KarelParser()

    if args.mode == 'text':
        for name in datasets:
            data_num = getattr(args, "{}_num".format(name))

            text = ""
            text_path = os.path.join(args.data_dir, "{}.txt".format(name))

            for _ in trange(data_num):
                code = parser.random_code(stmt_max_depth=args.max_depth)
                if args.beautify:
                    code = beautify(code)
                text += code  + "\n"

            with open(text_path, 'w') as f:
                f.write(text)
    else:
        for name in datasets:
            data_num = getattr(args, "{}_num".format(name))

            inputs, outputs, codes = [], [], []
            for _ in trange(data_num):
                while True:
                    parser.new_game(world_size=(args.world_width, args.world_height))
                    input = parser.get_state()

                    code = parser.random_code(stmt_max_depth=args.max_depth)

                    try:
                        parser.run(code)
                        output = parser.get_state()
                    except TimeoutError:
                        continue
                    except IndexError:
                        continue

                    inputs.append(input)
                    outputs.append(output)

                    if args.beautify:
                        code = beautify(code)
                    codes.append(code)

                    #pprint(code)
                    break

            npz_path = os.path.join(args.data_dir, name)
            np.savez(npz_path, inputs=inputs, outputs=outputs, codes=codes)
