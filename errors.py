# coding: utf8

from lisp import TextPosition


class LispError(Exception):
    """Generic Lisp error"""

    def __init__(self, msg: str, suggestion: str = None, program: str = None, start: TextPosition = None,
                 end: TextPosition = None, **kwargs):
        """
        Initializes a Lisp error
        :param msg: error message
        :param program: program text
        :param start: token start
        :param end: token end
        """
        preview = '% 4d  %s\n% 4s--' % (start.line, program.split('\n')[start.line - 1], '\\')

        for i in range(0, start.column - 1):
            preview += '-'

        for i in range(start.column, end.column):
            preview += '^'

        if start.column == end.column:
            preview += '^'

        suggestion = '. ¿Querías decir `%s`?' % suggestion if suggestion else ''
        super().__init__('%s en la línea %d, columna %d%s\n' % (msg, start.line, start.column, suggestion) + preview)
