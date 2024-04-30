import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyplume-dhi",
    version="0.0.1",
    author="Andy Banks",
    author_email="anba@dhigroup.com",
    description="A library for reading, manipulating, and analyzing TRDI ADCP data and SeaBird CTD data.", 
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=" ",
    packages=['pyplume','pyplume.pd0','pyplume.ctd','pyplume.plotting','pyplume.ptools','pyplume.pose','pyplume.data_manager'],#['pyplume','pyplume.pd0','pyplume.ctd','pyplume.plotting','pyplume.ptools','pyplume.data_manager','pyplume.data_visualizer','pyplume.pose']
    install_requires=[
        'numpy',
        'rich',
        'pandas',
        'matplotlib',
        'seaborn',
        'cmocean',
        'pyproj',
        'dill',
        'pathos',
        'progressbar',
        'cloudpickle',
	'psutil',
    ]   ,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

