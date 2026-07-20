from setuptools import find_packages, setup


setup(
    name="nexus-n3-plugin-cli",
    version="0.1.0",
    description="Developer CLI for scaffolding Nexus N3 plugins",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "nexus-n3-plugin-sdk>=0.1.0",
        "build>=1.2",
        "bleak>=0.22",
        "pyserial>=3.5",
        "pyzmq>=25.1",
    ],
    entry_points={
        "console_scripts": [
            "nexus-n3-plugin=nexus_n3_plugin_cli.main:main",
            "nx3-plugin=nexus_n3_plugin_cli.main:main",
        ],
    },
)
