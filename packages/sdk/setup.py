from setuptools import find_packages, setup


setup(
    name="rs-nexus-plugin-sdk",
    version="0.1.0",
    description="Shared SDK contracts for RS Nexus plugins",
    package_dir={"": "src"},
    packages=find_packages(
        where="src",
        exclude=[
            "rs_nexus_plugin_sdk.harness",
            "rs_nexus_plugin_sdk.harness.*",
        ],
    ),
    install_requires=[
        "PyYAML>=6.0",
    ],
)
