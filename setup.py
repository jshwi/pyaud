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
    author="Stephen Whitlock",
    email="stephen@jshwisolutions.com",
    copyright="2020, Stephen Whitlock",
    license="MIT",
    version="1.0.0",
    description="Makefile for Python",
    long_description=README,
    platforms="GNU/Linux",
    long_description_content_type="text/x-rst",
    url="https://github.com/jshwi/pyaud",
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    keywords="python3.9 Makefile make",
    packages=setuptools.find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "appdirs==1.4.4",
        "black==20.8b1",
        "codecov==2.1.9",
        "mypy==0.790",
        "object-colors==1.0.8",
        "pipfile-requirements==0.3.0",
        "pyblake2==1.1.2",
        "pyinstaller==4.1",
        "pylint==2.6.0",
        "pytest==6.2.1",
        "pytest-cov==2.10.1",
        "python-dotenv==0.15.0",
        "sphinx==3.3.1",
        "sphinxcontrib-fulltoc==1.2.0",
        "sphinxcontrib-programoutput==0.16",
        "vulture==2.1",
    ],
    entry_points={"console_scripts": ["pyaud=pyaud:main"]},
    python_requires=">=3.8",
)
