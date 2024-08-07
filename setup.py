"""A setuptools based setup module.

See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
"""

from setuptools import setup, find_packages
import pathlib

CHANGELOG = """
2.1.1-post3   Build system: Add a Makefile
"""

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")
version = CHANGELOG.strip().split()[0]

setup(
    name="umlsequence2",
    version=version,
    description="UML Sequence diagram generator from text input",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pbauermeister/umlsequence2",
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
    install_requires=["svgwrite", "svglib", "reportlab>=4.2.0"],
    extras_require={
        "dev": ["check-manifest"],
        "test": ["coverage"],
    },
    package_data={},
    entry_points={
        "console_scripts": [
            "umlsequence2=umlsequence2:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/pbauermeister/umlsequence2/issues",
        "Source": "https://github.com/pbauermeister/umlsequence2",
    },
)
