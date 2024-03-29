"""A setuptools based setup module.

See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
"""

from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="umlsequence2",
    version="2.0.6.post2",
    description="UML Sequence diagram generator from text input",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pbauermeister/dfd",
    author="Pascal Bauermeister",
    author_email="pascal.bauermeister@gmail.com",
    classifiers=[
        # https://pypi.org/classifiers/ :
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Information Technology",
        "Topic :: Software Development",
        "Topic :: Software Development :: Documentation",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
    ],
    keywords="diagram-generator, development, tool",
    license="GNU General Public License v3 (GPLv3)",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.10, <4",
    install_requires=["svgwrite", "svglib", "reportlab"],
    extras_require={
        "dev": ["check-manifest"],
        "test": ["coverage"],
    },
    package_data={
#        "umlsequence2": ["tbdpackage__data.dat"],
    },
#    data_files=[('data_flow_diagram', ["VERSION"])],
    # The following would provide a command called `umlsequence2` which
    # executes the function `main` from this package when invoked:
    entry_points={
        "console_scripts": [
            "umlsequence2=umlsequence2:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/pbauermeister/dfd/issues",
#        "Funding": "https://donate.pypi.org",
#        "Say Thanks!": "http://saythanks.io/to/example",
        "Source": "https://github.com/pbauermeister/dfd",
    },
)
