import os

from setuptools import setup


def read(fname):
    """
    Helper to read README
    """
    return open(os.path.join(os.path.dirname(__file__), fname)).read().strip()


ASSETS = "buzzword/static"
DOCS = "docs"

assets = [os.path.join(ASSETS, i) for i in os.listdir(ASSETS)]

docs = [os.path.join(DOCS, i) for i in os.listdir(DOCS)]

setup(
    name="buzzword",
    version="1.2.5",  # bump2version will edit this automatically!
    description="Web-app for corpus linguistics",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="Danny McDonald",
    include_package_data=True,
    zip_safe=False,
    packages=["buzzword", "docs", "explorer/parts"],
    package_dir={"explorer/parts/assets": "explorer/parts/assets", "docs": "docs"},
    scripts=["bin/buzzword", "bin/buzzword-create"],
    package_data={"buzzword/parts": assets, "docs": docs},
    data_files=[("explorer/parts/assets", assets), ("docs", docs)],
    author_email="daniel.mcdonald@uzh.ch",
    license="MIT",
    keywords=[],
    install_requires=[
        "buzz>=3.0.10",
        "python-dotenv==0.10.3",
        "flask==1.1.2",
        "dash==1.11.0",
        "dash-core-components==1.9.1",
        "dash-html-components==1.0.3",
        "dash-daq==0.5.0",
        "dash-renderer==1.4.0",
        "dash-table==4.6.2"`,
    ],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
)
