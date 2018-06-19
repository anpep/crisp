# coding: utf8

from typing import Union

from .types import *
from .env import *
from .parser import *


class VM(Parser):
    """The Lisp VM evaluates a program in a sandboxed environment"""

    def __init__(self):
        """Initializes the VM"""
        super(VM, self).__init__()

    def eval(self, value: Union[str, Expr], env: Env = None) -> Optional[Expr]:
        if env is None:
            # load default environment
            env = Env.get_std()

        if type(value) == str:
            # received a Python str to be evaluated
            return self.eval(self.parse(self.tokenize(value)), env)
        elif isinstance(value, Symbol):
            # set the Symbol environment and resolve its value if bound
            value.env = env
            return value.value
        elif isinstance(value, List) and value:
            # handle some special constructs
            if isinstance(value[0], Symbol):
                if value[0] in ('let', 'const'):
                    if not isinstance(value[1], List):
                        raise LispError('`%s` espera una lista de símbolos o pares símbolo-expresión' % value[0],
                                        List([value[0], List(map(lambda v: v.name, value[1:]))]) if all(
                                            isinstance(v, Text) for v in value[1:]) else '',
                                        **value[1].syntax_info)
                    env_update = dict()

                    for v in value[1]:
                        if isinstance(v, Symbol):
                            if v.is_lit:
                                raise LispError('no se puede utilizar un símbolo literal aquí', str(v)[1:],
                                                **v.syntax_info)

                            # bind nil to symbol v
                            env_update[v] = List()
                        elif isinstance(v, List):
                            if len(v) > 2:
                                raise LispError(
                                    'sobran elementos en la expresión `%s`' % value[0],
                                    program=v[2].syntax_info['program'],
                                    start=v[2].syntax_info['start'],
                                    end=v[-1].syntax_info['end'])
                            if not isinstance(v[0], Symbol):
                                raise LispError('se espera un par símbolo-expresión, no un par `%s`-expresión' %
                                                type(v[0]).__name__, **v[0].syntax_info)
                            if v[0].is_lit:
                                raise LispError('`%s` no admite un símbolo literal' % value[0],
                                                List((str(v[0])[1:], v[1])),
                                                **v[0].syntax_info)

                            env_update[v[0]] = v[1]
                        else:
                            raise LispError(
                                'se esperaba un símbolo o un par símbolo-expresión, no un valor del tipo `%s`' %
                                type(v).__name__, **v.syntax_info)

                    environment = env if env.outer is None else env.outer

                    for k, v in env_update.items():
                        val = self.eval(v, env)
                        environment.bind(k, val)
                        val._mutable = value[0] == 'let'

                    return List()
                elif value[0] in ('lambda', 'defun'):
                    symbol = None
                    arg_list = None
                    body = None

                    if value[0] == 'lambda':
                        if len(value) < 3:
                            raise LispError('la expresión `lambda` espera una lista de argumentos y un cuerpo',
                                            **value.syntax_info)
                        if len(value) > 3:
                            raise LispError(
                                'sobran elementos en la expresión `lambda`',
                                program=value[3].syntax_info['program'],
                                start=value[3].syntax_info['start'],
                                end=value[-1].syntax_info['end'])

                        arg_list = value[1]
                        body = value[2]
                    else:
                        if len(value) < 4:
                            raise LispError(
                                'la expresión `defun` espera un símbolo, una lista de argumentos y un cuerpo',
                                **value.syntax_info)
                        if len(value) > 4:
                            raise LispError(
                                'sobran elementos en la expresión `defun`',
                                program=value[4].syntax_info['program'],
                                start=value[4].syntax_info['start'],
                                end=value[-1].syntax_info['end'])

                        symbol = value[1]
                        arg_list = value[2]
                        body = value[3]

                        if not isinstance(symbol, Symbol):
                            raise LispError(
                                'se esperaba un símbolo como nombre de la función pero se obtuvo un valor del tipo `%s`' %
                                type(symbol).__name__, **symbol.syntax_info)
                        elif symbol.is_lit:
                            raise LispError(
                                'el nombre de la función no puede ser un símbolo literal. '
                                'Utiliza la notación `(lambda %s %s)` para declarar una función anónima' %
                                (repr(arg_list), repr(body)), **symbol.syntax_info)
                        elif symbol in env:
                            raise LispError('no es posible redeclarar un valor que ya está en el entorno',
                                            **symbol.syntax_info)

                    # validate signature
                    args = []
                    sig = []

                    for arg in arg_list:
                        if not isinstance(arg, Symbol):
                            raise LispError(
                                'se esperaba un símbolo como argumento pero se obtuvo un valor del tipo `%s`' %
                                type(arg).__name__, **arg.syntax_info)
                        elif arg.is_lit:
                            raise LispError('no se admiten símbolos literales como parámetros', str(arg)[1:],
                                            **arg.syntax_info)
                        elif args.count(arg):
                            raise LispError('el argumento `%s` no es único' % arg, **arg.syntax_info)

                        args.append(arg)
                        sig.append(Expr)

                    fn = None

                    if isinstance(body, Symbol):
                        body.env = env
                        if isinstance(body.value, Fn):
                            fn = Fn(Expr, *sig, callable=lambda *r, **s: body.value(*r, **s), expr=value,
                                    **value.syntax_info)

                    if not fn:
                        def fn(*params, **kwargs):
                            local_env = Env(env)
                            local_env.update(dict(zip(args, params)))
                            return self.eval(body, local_env)

                        fn = Fn(Expr, *sig, callable=fn, expr=value, **value.syntax_info)

                    if isinstance(symbol, Symbol):
                        environment = env if env.outer is None else env.outer
                        environment.bind(symbol, fn)
                        return List()
                    else:
                        return fn
                elif value[0] == 'while':
                    if len(value) == 1:
                        raise LispError('se esperaba una expresión condicional', **value[0].syntax_info)

                    result = List()
                    while True:
                        condition = self.eval(value[1], env)

                        if not isinstance(condition, Bool):
                            raise LispError(
                                'se esperaba un valor booleano pero la expresión devolvió un valor del tipo `%s`' %
                                type(condition).__name__, **value[1].syntax_info)
                        elif not condition:
                            break

                        result.append(
                            self.eval(List([e for e in value[2:]] if len(value) > 2 else [], **value.syntax_info), env))

                    return result

            # evaluate list
            value = List(map(lambda v: self.eval(v, Env(outer=env)), value), **value.syntax_info)

            # evaluate function call, if any
            if value and isinstance(value[0], Fn):
                return value[0](*value[1:],
                                **{**value[0].syntax_info, **dict(env=env if env.outer is None else env.outer)})

        return value
