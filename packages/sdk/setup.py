from setuptools import find_packages, setup


setup(
    name="rs-nexus-plugin-sdk",
    version="0.1.0",
    description="Shared SDK contracts for RS Nexus plugins",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "PyYAML>=6.0",
    ],
)
