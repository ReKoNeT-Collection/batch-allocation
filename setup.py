from setuptools import find_packages, setup

dependencies = open("requirements.txt", "r").read().splitlines()

setup(
    name='Komponentenbewertung',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=dependencies
)
