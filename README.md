# gerber_renderer

Python library for rendering RS274X gerber PCB files as svgs.

Installation: 
pip install gerber-renderer

Example Usage: 
from gerber_renderer import Gerber
board = Gerber.Board('filepath/gerber.zip', verbose=True) 
board.render('filepath/output') 
print(board.get_dimensions())
