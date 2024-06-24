from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in codiplus/__init__.py
from codiplus import __version__ as version

setup(
	name="codiplus",
	version=version,
	description="codi",
	author="codi",
	author_email="hassan@codi.cloud",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
