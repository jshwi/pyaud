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
    version="3.2.6",
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
        "black>=21.7b0",
        "codecov>=2.1.11, <=3.0.0",
        "coverage>=5.5, <=6.0",
        "docformatter>=1.4, <=2.0.0",
        "flynt>=0.64",
        "isort>=5.7.0, <=6.0.0",
        "mypy>=0.800",
        "object-colors>=2.0.0, <=3.0.0",
        "pipfile-requirements>=0.3.0",
        "pylint>=2.6.0, <=3.0.0",
        "pytest>=6.2.1, <=7.0.0",
        "pytest-cov>=2.11.1, <=3.0.0",
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
