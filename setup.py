import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
	long_description = fh.read()

setuptools.setup(
	name="acrome",
	version="0.4.0",
	author="Umut Ediz",
	author_email="umutediz@acrome.net",
	description="Hardware abstraction library for Acrome Robotics products",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/acrome-robotics/python-library",
	project_urls={
		"Bug Tracker": "https://github.com/acrome-robotics/python-library/issues",
    	},
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	],
	packages=setuptools.find_packages(exclude=['tests', 'test']),
	install_requires=["pyserial", "crccheck", "stm32loader==0.5.1", "requests", "packaging"],
	python_requires=">=3.7"
)
