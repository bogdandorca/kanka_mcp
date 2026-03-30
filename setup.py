import sys


NAME = "kanka-mcp-server"
VERSION = "0.1.0"


if __name__ == "__main__" and "--name" in sys.argv and len(sys.argv) == 2:
    print(NAME)
    raise SystemExit(0)

if __name__ == "__main__" and "--version" in sys.argv and len(sys.argv) == 2:
    print(VERSION)
    raise SystemExit(0)

from setuptools import find_packages, setup


setup(
    name=NAME,
    version=VERSION,
    packages=find_packages(exclude=("tests", "tests.*")),
    python_requires=">=3.10",
    install_requires=[
        "mcp>=1.0",
        "httpx>=0.27",
        "python-dotenv>=1.0",
        "uvicorn>=0.27",
    ],
    entry_points={
        "console_scripts": [
            "kanka-mcp-server=kanka_mcp_server.__main__:main",
        ],
    },
)
