from collections import namedtuple

TokenList = namedtuple('TokenList', 'input_expr tokens')
TextPosition = namedtuple('TextPosition', 'index line column')