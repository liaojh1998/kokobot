import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="kokobot",
    version="0.0.1",
    author="UT Austin SASE",
    author_email="jhliao@utexas.edu",
    description="Discord bot for UT Austin SASE",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/liaojh1998/kokobot",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
