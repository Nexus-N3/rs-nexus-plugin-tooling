from setuptools import find_packages, setup


setup(
    name="nexus-n3-plugin-sdk",
    version="0.1.0",
    description="Shared SDK contracts for Nexus N3 plugins",
    package_dir={"": "src"},
    packages=find_packages(
        where="src",
        exclude=[
            "nexus_n3_plugin_sdk.harness",
            "nexus_n3_plugin_sdk.harness.*",
        ],
    ),
    install_requires=[
        "PyYAML>=6.0",
    ],
)
