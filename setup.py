"""
setup
=====

``setuptools`` for package.
"""
import setuptools

with open("README.rst") as file:
    README = file.read()


setuptools.setup(
    name="pyaud",
    version="1.2.2",
    description="Automate quality-check of Python package with bundled utils",
    long_description=README,
    long_description_content_type="text/x-rst",
    author="Stephen Whitlock",
    email="stephen@jshwisolutions.com",
    maintainer="Stephen Whitlock",
    maintainer_email="stephen@jshwisolutions.com",
    url="https://github.com/jshwi/pyaud",
    copyright="2021, Stephen Whitlock",
    license="MIT",
    platforms="GNU/Linux",
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    keywords=[
        "python3.8",
        "audit",
        "deploy",
        "dev",
        "black",
        "codecov",
        "mypy",
        "pipfile-requirements",
        "pylint",
        "pytest",
        "pytest-cov",
        "sphinx",
        "vulture",
    ],
    packages=setuptools.find_packages(exclude=["tests", "tests.lib"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "appdirs==1.4.4",
        "black==20.8b1",
        "codecov==2.1.11",
        "coverage==5.3.1",
        "mypy==0.800",
        "object-colors==2.0.0",
        "pipfile-requirements==0.3.0",
        "pyblake2==1.1.2",
        "pylint==2.6.0",
        "pytest==6.2.1",
        "pytest-cov==2.11.1",
        "pytest-profiling==1.7.0",
        "pytest-randomly==3.5.0",
        "pytest-sugar==0.9.4",
        "sphinx==3.4.3",
        "sphinxcontrib-fulltoc==1.2.0",
        "sphinxcontrib-programoutput==0.16",
        "vulture==2.3",
    ],
    entry_points={"console_scripts": ["pyaud=pyaud:main"]},
    python_requires=">=3.8",
)
