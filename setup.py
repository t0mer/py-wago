from setuptools import setup, find_packages
from pathlib import Path

BASE_DIR = Path(__file__).parent
readme_path = BASE_DIR / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="py-wago",
    version="0.1.0",
    description="Async Python client library for the Wago WhatsApp API (MultiDevice)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    author="Tomer Klein",
    author_email="tomer.klein@gmail.com",
    url="https://github.com/t0mer/py-wago",
    download_url="https://pypi.org/project/py-wago/",
    packages=find_packages(exclude=("tests",)),
    python_requires=">=3.9",
    install_requires=[
        "aiohttp>=3.9",
        "pydantic>=2.0",
    ],
    keywords=["whatsapp", "api", "async", "wago", "client"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Framework :: AsyncIO",
        "Topic :: Communications :: Chat",
        "Typing :: Typed",
        "Operating System :: OS Independent",
    ],
)
