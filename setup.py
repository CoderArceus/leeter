from setuptools import setup, find_packages

setup(
    name="leeter",
    version="1.0.0",
    description="A powerful local C++ development tool for competitive programming.",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "fastapi",
        "uvicorn",
        "watchdog",
        "websockets",
        "requests",
        "beautifulsoup4"
    ],
    entry_points={
        "console_scripts": [
            "leeter=cli.leeter:main",
        ],
    },
)
