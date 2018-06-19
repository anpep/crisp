# coding: utf8

from . import *


class Parser:
    """The Parser tokenizes an input expression and translates it to an AST"""
    BRACES = {'(': ')', '[': ']'}
    BRACE_TYPES = {')': List, ']': Selector}

    WHITESPACE = ' \t\n'
    QUOTE = '"'
    DELIMITER = WHITESPACE + QUOTE + ''.join(BRACES.keys()) + ''.join(BRACES.values())
    ESCAPE = '\\'

    def parse(self, expr: TokenList) -> Expr:
        params = dict(program=expr.input_expr, start=TextPosition(0, 1, 1), end=TextPosition(0, 1, 1))

        if not expr.tokens:
            # empty input
            return List(**params)

        token = expr.tokens.pop(0)
        params['start'] = token['start']
        params['end'] = token['end']

        if token['type'] == 'punct':
            expr_list = List(**params)
            closing = self.BRACES[token['token']]  # character corresponding to the closing of this brace

            while expr.tokens[0]['type'] != 'punct' or expr.tokens[0]['token'] != closing:
                expr_list.append(self.parse(expr))

            expr.tokens.pop(0)
            return self.BRACE_TYPES[closing](expr_list, **params)
        elif token['type'] == 'lit':
            # string literal
            return String(token['token'], **params)
        elif token['type'] == 'atom':
            if token['token'] == 'nil':
                # return empty list
                return List(**params)
            elif token['token'] == 'true':
                return Bool(True, **params)
            elif token['token'] == 'false':
                return Bool(False, **params)

            try:
                if token['token'].startswith('0x'):
                    # parse hex number
                    return Real(float.fromhex(token['token']), **params)

                # decimal number?
                return Real(token['token'], **params)
            except ValueError:
                # this is just a Symbol
                return Symbol(token['token'], **params)

    def tokenize(self, expr: str) -> TokenList:
        tokens = []  # token list
        i = 0  # current index in expr
        line, column = 1, 1  # current text position
        atom = ''  # current atom
        braces = []  # position of opening braces

        # atom start values
        i0 = i
        line0, column0 = line, column

        while i < len(expr):
            if expr[i] in self.DELIMITER:
                if expr[i] in self.BRACES.keys():
                    braces.append(TextPosition(i, line, column))
                    tokens.append(dict(type='punct',
                                       token=expr[i],
                                       start=TextPosition(i, line, column),
                                       end=TextPosition(i + 1, line, column + 1)))
                elif expr[i] in self.BRACES.values():
                    if not braces:
                        # missing opening brace
                        raise LispError('no se esperaba un paréntesis',
                                        program=expr,
                                        start=TextPosition(i, line, column),
                                        end=TextPosition(i + 1, line, column + 1))

                    braces.pop()
                    tokens.append(dict(type='punct',
                                       token=expr[i],
                                       start=TextPosition(i, line, column),
                                       end=TextPosition(i + 1, line, column + 1)))
                elif expr[i] == self.QUOTE:
                    # save start values
                    i0 = i
                    line0, column0 = line, column

                    # move along the text position
                    if expr[i] == '\n':
                        column = 0
                        line += 1
                    column += 1
                    i += 1

                    while expr[i] != self.QUOTE:
                        # add character to the current atom
                        if expr[i] != self.ESCAPE:
                            atom += expr[i]
                        else:
                            # parse escape sequence
                            i += 1
                            if expr[i] == self.ESCAPE:
                                atom += self.ESCAPE
                            elif expr[i] == 'n':
                                atom += '\n'
                            elif expr[i] == 't':
                                atom += '\t'
                            elif expr[i] == '"':
                                atom += '"'
                            else:
                                raise LispError('no se reconoce esta secuencia de escape',
                                                program=expr,
                                                start=TextPosition(i, line, column),
                                                end=TextPosition(i + 1, line, column + 1))

                        # move along the text position
                        if expr[i] == '\n':
                            column = 0
                            line += 1
                        column += 1
                        i += 1

                        if i == len(expr):
                            # reached EOF and no closing quote was found
                            raise LispError('faltan las comillas de cierre',
                                            program=expr,
                                            start=TextPosition(i0, line0, column0),
                                            end=TextPosition(i0 + 1, line0, column0 + 1))

                    tokens.append(dict(type='lit',
                                       token=atom,
                                       start=TextPosition(i0, line0, column0),
                                       end=TextPosition(i, line, column)))
                    atom = ''

            elif expr[i] not in self.WHITESPACE:
                # save start values
                i0 = i
                line0, column0 = line, column

                while i < len(expr) and expr[i] not in self.WHITESPACE and expr[i] not in self.DELIMITER:
                    # add character to the current atom
                    atom += expr[i]
                    column += 1
                    i += 1

                tokens.append(dict(type='atom',
                                   token=atom,
                                   start=TextPosition(i0, line0, column0),
                                   end=TextPosition(i, line, column)))
                atom = ''

                column -= 1
                i -= 1

            # move along the text position
            if i < len(expr) and expr[i] == '\n':
                column = 0
                line += 1
            column += 1
            i += 1

        if braces:
            raise LispError('este paréntesis está abierto',
                            program=expr,
                            start=braces[-1],
                            end=braces[-1])

        return TokenList(expr, tokens)
