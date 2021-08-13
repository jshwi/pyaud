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
    version="3.2.3",
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
        "appdirs==1.4.4",
        "black==21.7b0",
        "codecov==2.1.12",
        "coverage==5.5",
        "docformatter==1.4",
        "flynt==0.65",
        "isort==5.9.0",
        "mypy==0.910",
        "object-colors==2.0.1",
        "pipfile-requirements==0.3.0",
        "pylint==2.9.6",
        "pytest-cov==2.12.1",
        "pytest==6.2.4",
        "python-dotenv==0.19.0",
        "readmetester==1.0.1",
        "sphinx==4.1.2",
        "sphinxcontrib-fulltoc==1.2.0",
        "sphinxcontrib-programoutput==0.17",
        "toml==0.10.2",
        "vulture==2.3",
    ],
    entry_points={"console_scripts": ["pyaud=pyaud.__main__:main"]},
    python_requires=">=3.8",
)
