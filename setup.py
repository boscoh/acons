import os

from setuptools import setup


def read(*rnames):
    with open(os.path.join(os.path.dirname(__file__), *rnames)) as f:
        return f.read()


setup(
    name="acons",
    version="0.1",
    author="Bosco Ho",
    author_email="apposite@gmail.com",
    url="https://github.com/boscoh/acons",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    py_modules=["acons"],
    install_requires=["fastapi", "uvicorn", "pylru"],
    description="Async command-line runner",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Libraries",
        "Topic :: Utilities",
    ]
)
