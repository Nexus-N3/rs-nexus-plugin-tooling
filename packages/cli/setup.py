from setuptools import find_packages, setup


setup(
    name="rs-nexus-plugin-cli",
    version="0.1.0",
    description="Developer CLI for scaffolding RS Nexus plugins",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "rs-nexus-plugin-sdk>=0.1.0",
    ],
    entry_points={
        "console_scripts": [
            "rsnexus-plugin=rs_nexus_plugin_cli.main:main",
        ],
    },
)
