"""
setup
=====

``setuptools`` for package.
"""
import setuptools

with open("README.rst", encoding="utf-8") as file:
    README = file.read()


setuptools.setup(
    name="pyaud",
    version="3.6.0",
    description="Framework for writing Python packages audits",
    long_description=README,
    long_description_content_type="text/x-rst",
    author="Stephen Whitlock",
    author_email="stephen@jshwisolutions.com",
    url="https://github.com/jshwi/pyaud",
    license="MIT",
    platforms="GNU/Linux",
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    keywords=[
        "audit",
        "black",
        "codecov",
        "coverage",
        "docformatter",
        "flynt",
        "isort",
        "mypy",
        "pipfile-requirements",
        "pylint",
        "pytest-cov",
        "pytest",
        "python3.8",
        "readmetester",
        "sphinx",
        "toml",
        "vulture",
    ],
    packages=setuptools.find_packages(exclude=["tests"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "appdirs>=1.4.4, <=2.0.0",
        # see
        # https://github.com/pypa/pipenv/issues/1760#issuecomment-527366599
        #
        # in short, without strong equality running `pipenv lock` with
        # this as a dependency will fail (unless passing `--pre` as an
        # argument)
        #
        # - ERROR: Could not find a version that matches black>=21.7b0
        #   Skipped pre-versions
        #
        # appears the version needs to be strictly specified in order
        # for `pipenv` to allow locking without the additional argument
        # this adds extra time to the locking process if forgotten, and
        # the error message could be confusing to some
        "black==21.12b0",
        "codecov>=2.1.11, <=3.0.0",
        "coverage>=5.0.0, <=7.0.0",
        "docformatter>=1.4, <=2.0.0",
        "environs>=9.0.0, <=10.0.0",
        "flynt>=0.64",
        "isort>=5.7.0, <=6.0.0",
        "m2r>=0.2.1, <=1.0.0",
        "mistune<=0.8.4",
        "mypy>=0.800",
        "object-colors>=2.0.0, <=3.0.0",
        "pipfile-requirements>=0.3.0",
        "pylint>=2.6.0, <=3.0.0",
        "pytest>=6.2.1, <=7.0.0",
        "pytest-cov>=2.0.0, <=4.0.0",
        "python-dotenv>=0.16.0",
        "readmetester>=1.0.0, <=2.0.0",
        "sphinx>=4.1.2, <=5.0.0",
        "sphinxcontrib-fulltoc>=1.2.0, <=2.0.0",
        "sphinxcontrib-programoutput>=0.16",
        "toml>=0.10.2",
        "vulture>=2.3, <=3.0",
    ],
    entry_points={"console_scripts": ["pyaud=pyaud.__main__:main"]},
    python_requires=">=3.8",
)
