# gerber_renderer

Python library for rendering RS274X gerber PCB files as svgs or pdfs.

<main class="col-12 col-md-9 col-xl-7 py-md-5 pl-md-5 pr-md-4 bd-content" role="main">

                <div>

                    <div class="section" id="installation">
                        <span id="install"></span>
                        <h1>Installation</h1>
                        <p>The easiest way to install pandas is to install it
                            via pip from <a class="reference external"
                                href="https://pypi.org/project/gerber-renderer/">PyPI</a>.</p>
                        <p>Officially Python 3.6 and above.</p>
                    </div>

                    <div class="section" id="installing-from-pypi">
                        <h3>Installing from PyPI</h3>
                        <div class="highlight-default notranslate">
                            <div class="highlight">
                                <pre><span></span><span class="n">pip</span> <span class="n">install</span> <span class="n">gerber-renderer</span></pre>
                            </div>
                        </div>

                        <div class="section" id="dependencies">
                            <span id="install-dependencies"></span>
                            <h2>Dependencies</h2>
                            <table class="table">
                                <colgroup>
                                    <col style="width: 71%">
                                    <col style="width: 29%">
                                </colgroup>
                                <thead>
                                    <tr class="row-odd">
                                        <th class="head">
                                            <p>Package</p>
                                        </th>
                                        <th class="head">
                                            <p>Minimum supported version</p>
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr class="row-even">
                                        <td>
                                            <p><a class="reference external"
                                                    href="https://pypi.org/project/svgwrite/">svgwrite</a>
                                            </p>
                                        </td>
                                        <td>
                                            <p>1.4</p>
                                        </td>
                                    </tr>
                                    <tr class="row-odd">
                                        <td>
                                            <p><a class="reference external"
                                                    href="https://pypi.org/project/svglib/">svglib</a></p>
                                        </td>
                                        <td>
                                            <p>1.0</p>
                                        </td>
                                    </tr>
                                    <tr class="row-even">
                                        <td>
                                            <p><a class="reference external"
                                                    href="https://pypi.org/project/reportlab/">reportlab</a>
                                            </p>
                                        </td>
                                        <td>
                                            <p>3.5</p>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                            <div class="section" id="installation">
                                <span id="usage"></span>
                                <h1>Usage</h1>
                                <p>Gerber Renderer is a Python library for rendering RS274X gerber PCB files as svgs or
                                    pdfs.</p>
                            </div>
                            <div class="section" id="installing-from-pypi">
                                <h3>Importing</h3>
                                <pre><span></span><span class="n">from gerber_renderer import Gerber</span></pre>
                            </div>
                            <div class="section" id="installing-from-pypi">
                                <h3>Functions</h3>
                                <div class="highlight-default notranslate">
                                    <h4>Initialize</h4>
                                    <pre><span></span><span class="n">board = Gerber.Board(file=file_path, max_height=XXX, verbose=True)</span></pre>
                                    <p>
                                        <b>file:</b> string representing the relative path to the root folder
                                        containing
                                        the gerber files
                                        <br>
                                        <b>max_height:</b> integer representing the maximum height (in pixels) of
                                        the
                                        rendered svg (default=500px)
                                        <br>
                                        <b>verbose:</b> outputs info about the current progress to the terminal
                                        (default=False)
                                    </p>
                                    <h4>Render SVG</h4>
                                    <pre><span></span><span class="n">board.render(output=output_path)</span></pre>
                                    <p>
                                        <b>output:</b> string representing the relative path to the root folder
                                        to save the svg files to
                                    </p>

                                </div>
                                <div class="section" id="installation">
                                    <span id="examples"></span>
                                    <h1>Examples</h1>
                                    <pre><span></span><span class="n">from gerber_renderer import Gerber<br><br>board = Gerber.Board('./tests/gerber.zip', verbose=True)<br>board.render('./tests/output')</span></pre>
                                </div>



            </main>