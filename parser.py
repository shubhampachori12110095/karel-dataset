from __future__ import print_function

import yacc
import numpy as np
import ply.lex as lex

from main import Karel
from utils import pprint, timeout

def dummy():
    pass

class Parser(object):
    """
    Base class for a lexer/parser that has the rules defined as methods
    """
    tokens = ()
    precedence = ()

    def __init__(self, **kwargs):
        self.names = {}
        self.debug = kwargs.get('debug', 0)

        # Build the lexer and parser
        lex.lex(module=self, debug=self.debug)
        _, self.grammar = yacc.yacc(
                module=self, debug=self.debug,
                tabmodule='_parsetab', with_grammar=True)

        self.prodnames = self.grammar.Prodnames

class KarelParser(Parser):

    tokens = [
            'DEF', 'RUN', 
            'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'SEMI', 'INT', #'NEWLINE',
            'WHILE', 'REPEAT',
            'IF', 'IFELSE', 'ELSE',
            'FRONTISCLEAR', 'LEFTISCLEAR', 'RIGHTISCLEAR',
            'MARKERSPRESENT', 'NOMARKERSPRESENT', 'NOT',
            'MOVE', 'TURNRIGHT', 'TURNLEFT',
            'PICKMARKER', 'PUTMARKER',
    ]

    t_ignore =' \t\n'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_LBRACE = r'\{'
    t_RBRACE = r'\}'
    t_SEMI   = r';'

    t_DEF = 'def'
    t_RUN = 'run'
    t_WHILE = 'while'
    t_REPEAT = 'repeat'
    t_IF = 'if'
    t_IFELSE = 'ifelse'
    t_ELSE = 'else'
    t_NOT = 'not'

    t_FRONTISCLEAR = 'front_is_clear'
    t_LEFTISCLEAR = 'left_is_clear'
    t_RIGHTISCLEAR = 'right_is_clear'
    t_MARKERSPRESENT = 'markers_present'
    t_NOMARKERSPRESENT = 'no_markers_present'

    t_MOVE = 'move'
    t_TURNRIGHT = 'turn_right'
    t_TURNLEFT = 'turn_left'
    t_PICKMARKER = 'pick_marker'
    t_PUTMARKER = 'put_marker'


    def __init__(self, rng=None, min_int=0, max_int=19, debug=False, **kwargs):
        super(KarelParser, self).__init__(**kwargs)

        self.debug = debug
        self.min_int = min_int
        self.max_int = max_int

        if rng is None:
            self.rng = np.random.RandomState(1)
        else:
            self.rng = rng


    #########
    # lexer
    #########

    def t_INT(self, t):
        r'\d+'

        value = int(t.value)
        if not (self.min_int <= value <= self.max_int):
            raise Exception(" [!] Out of range ({} ~ {}): `{}`". \
                    format(self.min_int, self.max_int, value))

        t.value = value
        return t

    def random_INT(self):
        return self.rng.randint(self.min_int, self.max_int + 1)

    def t_error(self, t):
        print("Illegal character %s" % repr(t.value[0]))
        t.lexer.skip(1)

    #########
    # parser
    #########

    def p_prog(self, p):
        '''prog : DEF RUN LPAREN RPAREN LBRACE stmt RBRACE'''
        stmt = p[6]
        p[0] = lambda: stmt()

    def p_stmt(self, p):
        '''stmt : while
                | repeat
                | stmt_stmt
                | action
                | if
                | ifelse
        '''
        fn = p[1]
        p[0] = lambda: fn()

    def p_stmt_stmt(self, p):
        '''stmt_stmt : stmt SEMI stmt
        '''
        stmt1, stmt2 = p[1], p[3]
        def fn():
            stmt1(); stmt2();
        p[0] = fn

    def p_if(self, p):
        '''if : IF LPAREN cond RPAREN LBRACE stmt RBRACE
        '''
        cond, stmt = p[3], p[6]
        p[0] = lambda: stmt() if cond() else dummy()

    def p_ifelse(self, p):
        '''ifelse : IFELSE LPAREN cond RPAREN LBRACE stmt RBRACE ELSE LBRACE stmt RBRACE
        '''
        cond, stmt1, stmt2 = p[3], p[6], p[10]
        p[0] = lambda: stmt1() if cond() else stmt2()

    def p_while(self, p):
        '''while : WHILE LPAREN cond RPAREN LBRACE stmt RBRACE
        '''
        cond, stmt = p[3], p[6]
        def fn():
            while(cond()):
                stmt()
        p[0] = fn

    def p_repeat(self, p):
        '''repeat : REPEAT LPAREN cste RPAREN LBRACE stmt RBRACE
        '''
        cste, stmt = p[3], p[6]
        def fn():
            for _ in range(cste()):
                stmt()
        p[0] = fn

    def p_cond(self, p):
        '''cond : cond_without_not
                | NOT cond_without_not
        '''
        if callable(p[1]):
            cond_without_not = p[1]
            p[0] = lambda: cond_without_not()
        else: # NOT
            cond_without_not = p[2]
            p[0] = lambda: not cond_without_not()

    def p_cond_without_not(self, p):
        '''cond_without_not : FRONTISCLEAR LPAREN RPAREN
                            | LEFTISCLEAR LPAREN RPAREN
                            | RIGHTISCLEAR LPAREN RPAREN
                            | MARKERSPRESENT LPAREN RPAREN 
                            | NOMARKERSPRESENT LPAREN RPAREN
        '''
        cond_without_not = p[1]
        p[0] = lambda: getattr(self.karel, cond_without_not)()

    def p_action(self, p):
        '''action : MOVE LPAREN RPAREN
                  | TURNRIGHT LPAREN RPAREN
                  | TURNLEFT LPAREN RPAREN
                  | PICKMARKER LPAREN RPAREN
                  | PUTMARKER LPAREN RPAREN
        '''
        action = p[1]
        def fn():
            return getattr(self.karel, action)()
        p[0] = fn

    def p_cste(self, p):
        '''cste : INT
        '''
        value = p[1]
        p[0] = lambda: int(value)

    def p_empty(self, p):
        """empty :"""

    def p_error(self, p):
        if p:
            print("Syntax error at '%s'" % p.value)
        else:
            print("Syntax error at EOF")

    #########
    # Karel
    #########

    def get_state(self):
        return self.karel.state

    @timeout(0.001)
    def run(self, code, **kwargs):
        return yacc.parse(code, **kwargs)()

    def new_game(self, **kwargs):
        self.karel = Karel(debug=self.debug, **kwargs)

    def draw(self, *args, **kwargs):
        self.karel.draw(*args, **kwargs)

    def random_code(self, *args, **kwargs):
        return " ".join(self.random_tokens(*args, **kwargs))

    def random_tokens(self, start_token="prog", depth=0, stmt_max_depth=5):
        if start_token == 'stmt' and depth > stmt_max_depth:
            start_token = "action"

        codes = []
        candidates = self.prodnames[start_token]

        prod = candidates[self.rng.randint(len(candidates))]

        for term in prod.prod:
            if term in self.prodnames: # need digging
                codes.extend(self.random_tokens(term, depth + 1, stmt_max_depth))
            else:
                token = getattr(self, 't_{}'.format(term))
                if callable(token):
                    if token == self.t_INT:
                        token = self.random_INT()
                    else:
                        raise Exception(" [!] Undefined token `{}`".format(token))

                codes.append(str(token).replace('\\', ''))

        return codes

def test(parser, code=None):
    if code is None:
        code = parser.random_code()
        pprint(code)
    elif code.strip() == "":
        return

    parser.new_game(world_size=(8, 8))

    parser.draw("Input:  ")
    parser.run(code, debug=False)
    parser.draw("Output: ")
