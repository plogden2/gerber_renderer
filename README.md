<div class="container-xl">
        <div class="row">
            <div class="col-12 col-md-2 bd-sidebar">
                <nav class="bd-links" id="bd-docs-nav" aria-label="Main navigation">
                    <div class="bd-toc-item active">
                        <ul class="nav bd-sidenav">
                            <li class="">
                                <a href="#installation">Installation</a>
                            </li>
                            <li class="">
                                <a href="#usage">
                                    Usage</a>
                            </li>
                            <li class="">
                                <a href="#examples">Examples</a>
                            </li>
                        </ul>
                    </div>
                </nav>
            </div>
        </div>
</div>

## Gerber Renderer

Python library for rendering RS274X gerber PCB files as svgs or pdfs.

## Table of contents

- [Installation](#installation)
- [Usage](#usage)
- [What's included](#examples)

Installation: 
pip install gerber-renderer

Example Usage: 
from gerber_renderer import Gerber
board = Gerber.Board('filepath/gerber.zip', verbose=True) 
board.render('filepath/output') 
print(board.get_dimensions())
