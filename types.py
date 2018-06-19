# coding: utf8

import math
import numbers
import re
import string

from collections import namedtuple
from functools import reduce
from typing import Callable, Optional, Text, List as _List
from . import *

IDENTIFIER = re.compile(r'^[^0-9\'][^\']*$')


class Expr:
    """A symbolic expression is an Atom or a List"""
    # full text of the program
    _program: str

    # index, line and column in the text buffer where the expression starts
    _start: TextPosition

    # index, line and column in the text buffer where the expression ends
    _end: TextPosition

    # environment corresponding to this expression
    env: dict = None

    def __init__(self, *args, **kwargs):
        """
        Initializes a symbolic expression instance
        :param program: full program text
        :param start: index, line and column in the text buffer where the expression starts
        :param end: index, line and column in the text buffer where the expression ends
        """
        if {'program', 'start', 'end'} <= set(kwargs):
            self._program = kwargs['program']
            self._start = kwargs['start']
            self._end = kwargs['end']

    """def __repr__(self) -> Optional[Text]:
        ""Returns the string representation for this expression""
        return self._program[self._start.index:self._end.index] \
            if all((self._program, self._start, self._end)) \
            else None"""

    def bind_syntax_info(self, program: str, start: TextPosition, end: TextPosition):
        """Binds syntactic information to this expression """
        self._program = program
        self._start = start
        self._end = end

    @property
    def syntax_info(self) -> dict:
        """Returns a dictionary with syntactic information for this expression"""
        return dict(program=self._program, start=self._start, end=self._end)

    @property
    def start(self) -> Optional[TextPosition]:
        """Returns the index, line and column in the text buffer where the expression starts"""
        return self._start

    @property
    def end(self) -> Optional[TextPosition]:
        """Returns the index, line and column in the text buffer where the expression end"""
        return self._end


class Atom(Expr):
    """An Atom is a Symbol, a Real or a String"""
    _mutable: bool

    def __init__(self, mutable: bool = True, *args, **kwargs):
        """
        Initializes a new Atom
        :param mutable: if True this Atom value will be treated as mutable
        """
        super().__init__(*args, **kwargs)
        self._mutable = mutable

    @property
    def is_mut(self) -> bool:
        """Determines whether this Atom is mutable or not"""
        return self._mutable


class List(Expr, _List[Expr]):
    """A List is a set of Atoms or Lists"""

    def __init__(self, *args, **kwargs):
        list.__init__(self, *args)
        Expr.__init__(self, **kwargs)

    def __str__(self) -> str:
        """Returns a string containing all the elements of this List"""
        return '(' + ' '.join(repr(el) for el in self) + ')' if self else 'nil'

    def __repr__(self) -> str:
        """Returns the string representation of this LIst"""
        return str(self)


class Symbol(Atom, Text):
    """A Symbol is an identifier that can be resolved to a value"""
    # if True, this is a literal (quoted) symbol and may not be resolved to a value
    _lit: bool = False

    # name of this symbol
    _name: str = None

    # environment for symbol resolution
    env: dict = {}

    def __new__(cls, name: any, *args, **kwargs):
        """Creates a new Symbol"""
        name = str(name)

        lit = name[0] == "'"
        name = name[1:] if lit else name

        self = Text.__new__(cls, name)
        self._lit = lit
        self._name = name

        if not IDENTIFIER.match(self):
            suggestion = ("'" if lit else '') + name.replace("'", '').lstrip(string.digits)
            raise LispError('`%s` no es un identificador válido' % self, suggestion, **kwargs)

        return self

    def __init__(self, *args, **kwargs):
        """Initializes a new Symbol"""
        super().__init__(*args, **kwargs)

    def __str__(self):
        """Returns the Symbol string"""
        return ("'" if self._lit else '') + self._name

    def __repr__(self):
        """Returns the string containing the representation of this symbol"""
        return str(self)

    @property
    def is_lit(self) -> bool:
        """Returns True if this is a quoted Symbol"""
        return self._lit

    @property
    def name(self) -> str:
        """Returns the name of this symbol"""
        return self._name

    @property
    def value(self) -> any:
        """Returns the value bound to this Symbol"""
        value = self if self._lit else self.env[self]
        value.bind_syntax_info(**self.syntax_info)
        return value


class String(Atom, Text):
    """A String is an ordered sequence of bytes"""

    def __new__(cls, *args, **kwargs):
        """Creates a new String"""
        return str.__new__(cls, *args)

    def __init__(self, *args, **kwargs):
        """Initializes a new String"""
        super().__init__(**kwargs)

    def __repr__(self):
        """Returns the evaluable representation of this string"""
        return '"' + str(self).replace('\n', '\\n') \
            .replace('\t', '\\t') \
            .replace('\\', '\\\\') \
            .replace('"', '\\"') + '"'


class Real(Atom, float):
    """A Real is a floating-point value"""

    def __new__(cls, *args, **kwargs):
        """Creates a new Real value"""
        return float.__new__(cls, *args)

    def __init__(self, *args, **kwargs):
        """Initializes a new Real value"""
        Atom.__init__(self, **kwargs)

    def __str__(self) -> str:
        """Converts the Real value to a string"""
        return '%g' % self


class Bool(Atom):
    """A Bool can take two values: true or false"""
    _true: bool

    def __init__(self, value: bool, *args, **kwargs):
        """Initializes a new Bool"""
        super().__init__(*args, **kwargs)
        self._true = value

    def __bool__(self) -> bool:
        """Evaluates to True if this Bool is `true`"""
        return self._true

    def __eq__(self, other) -> bool:
        return other._true == self._true

    def __repr__(self) -> str:
        """Returns the string representation of this Bool"""
        return 'true' if self else 'false'

    def __str__(self):
        """Converts this Bool to a String"""
        return repr(self)


class Selector(List):
    """A Selector is a special List used to query properties and values from Lists and Atoms"""
    pass


class Fn(Atom, Callable):
    """
    A Fn is a callable function which is defined by a Python function or method
    """

    class ParameterTypeList:
        """
        The ParameterTypeList type wraps the type definitions of a Fn's parameter list
        """
        # list of types
        _types: [..., type]

        # index of the first ellipsis
        _ellipsis_index: int = -1

        def __init__(self, types: [..., type] = ()):
            """Initializes the parameter type list"""
            super().__init__()
            self._types = types

            try:
                self._ellipsis_index = types.index(...)
            except ValueError:
                self._ellipsis_index = -1

        def __getitem__(self, index: int):
            """Retrieves a type from this list"""
            if self._ellipsis_index != -1 and index >= self._ellipsis_index:
                return self._types[self._ellipsis_index + 1]

            return self._types[index]

        def __len__(self):
            """Obtains the length of the parameter list"""
            return len(self._types)

        @property
        def has_ellipsis(self) -> bool:
            """Returns True if this parameter list has an ellipsis"""
            return self._ellipsis_index > -1

    # Fn return type
    _return_type: type

    # parameter list
    _signature: ParameterTypeList

    # callable object
    _callable: Callable

    # original expression (if any)
    _expr: Expr

    def __init__(self, return_type: type, *signature: [..., type], callable: Callable, expr: Expr = None, **kwargs):
        """Initializes this Fn"""
        super().__init__(**kwargs)
        self._return_type = return_type
        self._signature = self.ParameterTypeList(signature)
        self._callable = callable
        self._expr = expr

    def __call__(self, *args, **kwargs):
        """Evaluates this Fn"""
        # check arity
        if len(args) > len(self._signature) and not self._signature.has_ellipsis:
            raise LispError('la función esperaba %d argumentos, pero se pasaron %d' %
                            (len(self._signature), len(args)), **kwargs)

        # perform type check in positional arguments
        for i in range(0, len(args)):
            if not isinstance(args[i], self._signature[i]):
                raise LispError('la función esperaba un argumento del tipo `%s`, pero se pasó uno del tipo `%s`' %
                                (self._signature[i].__name__, type(args[i]).__name__), **args[i].syntax_info)

        return_value = Fn._normalize(self._callable(*args, **kwargs))

        # check return value type
        if not isinstance(return_value, self._return_type):
            raise LispError('la función intentó devolver un valor del tipo `%s` declarando un tipo de retorno `%s`' %
                            (type(return_value).__name__, type(self._return_type).__name__), **kwargs)

        return return_value

    def __str__(self):
        return str(self._expr) if self._expr else '<Fn>'

    @staticmethod
    def _normalize(value: any) -> Expr:
        """Normalizes a value"""

        if isinstance(value, Expr):
            return value
        if isinstance(value, list) or isinstance(value, set) or isinstance(value, tuple):
            return List(value)
        if isinstance(value, dict):
            return List(reduce(lambda k, v: k + v, value.items()))
        if isinstance(value, bool):
            return Bool(value)
        if isinstance(value, numbers.Real):
            return Real(value)
        if isinstance(value, str):
            return String(value)
        if value is None:
            return List()
        return value
