import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gerber_renderer",  # Replace with your own username
    version="0.0.35",
    author="Patrick Ogden",
    author_email="plogden2@gmail.com",
    description="A library for rendering gerber files as SVGs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Pitwuk/gerber_renderer",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        'svgwrite >= 1.4'
    ]
)
