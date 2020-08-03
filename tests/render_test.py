from gerber_renderer import renderer


board = renderer.Gerber('./tests/gerber.zip', verbose=True)
print(board.get_dimensions())
