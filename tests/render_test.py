from gerber_renderer import Gerber

board = Gerber.Board('./tests/gerber.zip', verbose=True)
board.render('./tests/output')
print(board.get_dimensions())
