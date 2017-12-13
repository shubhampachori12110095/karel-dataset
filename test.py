from __future__ import print_function

from prompt_toolkit import prompt

if __name__ == '__main__':
    answer = prompt(u'Give me some input: ')
    print('You said: %s' % answer)
