import importlib.util
spec = importlib.util.spec_from_file_location(
    "Gerber", ".\gerber_renderer\Gerber.py")
Gerber = importlib.util.module_from_spec(spec)
spec.loader.exec_module(Gerber)

board = Gerber.Board('./tests/gerber3.zip', verbose=True)
board.render('./tests/output')
board.render_pdf('./tests/output', 'top_copper',
                 'white', scale_compensation=-0.206, full_page=True, offset=(200, -250))
board.render_pdf('./tests/output', 'bottom_copper',
                 'white', mirrored=True, scale_compensation=-0.206, full_page=True, offset=(0, -0))
board.render_pdf('./tests/output', 'top_mask',
                 'black', mirrored=True, scale_compensation=-0.206,  full_page=True)
board.render_pdf('./tests/output', 'top_mask',
                 'black', scale_compensation=-0.206, full_page=True)
# board.render_pdf('./tests/output', 'top_silk', 'yellow')
