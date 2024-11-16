from setuptools import setup, find_packages

setup(
    name = "libeduwm",
    version = "0.0.1",
    license = "MIT",
    url = "http://github.com/MagnuSiwy/eduWm",
    author = "Kacper Magnuszewski | Robert Gaweł",
    description = "Window Manager for newbies",
    packages = find_packages(),
    install_requires = [
        "pyyaml",
        "xcffib",
        "xpybutil"
    ],
    classifiers = [
        "Programming Language :: Python",
        "Operating System :: POSIX :: Linux"
    ],
    keywords = ["python", "eduWM", "Linux", "newcomer", "newbie"],
    python_requires = ">=3.6"
)


