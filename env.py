# coding: utf8

import math
import functools
import operator

from .types import *


class Env(dict):
    outer = None

    def __init__(self, outer=None):
        dict.__init__(self)
        if isinstance(outer, Env):
            self.outer = outer

    def bind(self, k, v):
        dict.__setitem__(self, k, v)

    def __getitem__(self, k):
        if dict.__contains__(self, k):
            return dict.__getitem__(self, k)
        if isinstance(self.outer, Env):
            return self.outer[k]
        raise LispError('`%s` no pertenece al entorno' % k, **k.syntax_info)

    def __setitem__(self, k, v):
        if dict.__contains__(self, k):
            dict.__setitem__(self, k, v)
        elif isinstance(self.outer, Env):
            self.outer.__setitem__(k, v)
        raise LispError('`%s` no pertenece al entorno' % k, **k.syntax_info)

    def __contains__(self, k):
        if dict.__contains__(self, k):
            return True
        if isinstance(self.outer, Env):
            return self.outer.__contains__(k)
        return False

    @staticmethod
    def get_std():
        """Returns the standard environment"""
        std_env = Env()
        std_env.update({
            Symbol('e'): Real(math.e),
            Symbol('inf'): Real(math.inf),
            Symbol('nan'): Real(math.nan),
            Symbol('pi'): Real(math.pi),
            Symbol('tau'): Real(math.tau),

            Symbol('send'): Fn(List, ..., Expr, callable=lambda *r, **s: print(*r)),
            Symbol('sendf'): Fn(List, String, ..., Expr, callable=lambda f, *r, **s: print(f % r)),

            Symbol('set'): Fn(Expr, Symbol, Expr, callable=Env.set),
            Symbol('apply'): Fn(Expr, Fn, List, callable=lambda f, l, **s: f(*l)),

            Symbol('+'): Fn(Real, ..., Real, callable=lambda *r, **s: sum(r)),
            Symbol('-'): Fn(Real, ..., Real, callable=lambda *r, **s: r[0] + -sum(r[1:])),
            Symbol('*'): Fn(Real, ..., Real, callable=lambda *r, **s: functools.reduce(operator.mul, r, 1)),
            Symbol('/'): Fn(Real, ..., Real, callable=lambda *r, **s: functools.reduce(operator.truediv, r[1:], r[0])),

            Symbol('<'): Fn(Bool, Real, Real, callable=lambda a, b, **s: a < b),
            Symbol('<='): Fn(Bool, Real, Real, callable=lambda a, b, **s: a <= b),
            Symbol('>'): Fn(Bool, Real, Real, callable=lambda a, b, **s: a > b),
            Symbol('>='): Fn(Bool, Real, Real, callable=lambda a, b, **s: a >= b),

            Symbol('='): Fn(Bool, object, object, callable=Env.strict_eq),
            Symbol('!='): Fn(Bool, object, object, callable=lambda a, b, **s: not Env.strict_eq(a, b)),

            Symbol('!'): Fn(Bool, Bool, callable=lambda v, **s: not v),
            Symbol('&&'): Fn(Bool, ..., Bool,
                             callable=lambda *r, **s: functools.reduce(lambda a, b: a and b, r, Bool(True))),
            Symbol('||'): Fn(Bool, ..., Bool,
                             callable=lambda *r, **s: functools.reduce(lambda a, b: a or b, r, Bool(False))),

            Symbol('~'): Fn(Real, Real, callable=lambda n, **s: Real(float(~int(n)))),
            Symbol('&'): Fn(Real, ..., Real,
                            callable=lambda *r, **s: functools.reduce(lambda a, b: int(a) & int(b), r, -1)),
            Symbol('|'): Fn(Real, ..., Real,
                            callable=lambda *r, **s: functools.reduce(lambda a, b: int(a) | int(b), r, -1))
        })

        return std_env

    @staticmethod
    def strict_eq(a: Expr, b: Expr, **kwargs) -> Bool:
        if type(a) != type(b):
            raise LispError('no se puede comparar un valor del tipo `%s` a otro del tipo `%s`' %
                            (type(b).__name__, type(a).__name__), **kwargs)
        return Bool(a == b)

    @staticmethod
    def set(sym: Symbol, value: Expr, env: dict, **kwargs) -> Expr:
        env[sym]
        env.bind(Symbol(sym.name, **sym.syntax_info), value)
        return env[sym]
