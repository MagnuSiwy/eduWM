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
        "xcffib",
        "xpybutil",
        "gi",
        "PIL",
    ],
    classifiers = [
        "Programming Language :: Python",
        "Operating System :: POSIX :: Linux"
    ],
    keywords = ["python", "eduWM", "Linux", "newcomer", "newbie", "window manager", "wm"],
    python_requires = ">=3.6"
)


