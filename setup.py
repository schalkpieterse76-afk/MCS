from setuptools import setup, find_packages

setup(
    name="mcs_cvor",
    version="1.0.0",
    description="MCS CVOR Remote Management System for SAAF",
    author="MCS",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "PyQt6>=6.6.0",
        "PyQt6-WebEngine>=6.6.0",
        "SQLAlchemy>=2.0.0",
        "folium>=0.15.0",
        "psutil>=5.9.0",
    ],
    entry_points={
        "console_scripts": [
            "mcs-cvor=mcs_cvor.main:main",
        ],
    },
)
