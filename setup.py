from setuptools import setup, find_packages

setup(
    name="pygeosetter",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'PyQt5>=5.15.0',
        'Pillow>=8.0.0',
        'piexif>=1.1.3',
        'folium>=0.12.0',
        'exifread>=2.3.2',
        'geopy>=2.2.0',
    ],
    entry_points={
        'console_scripts': [
            'pygeosetter=pygeosetter.__main__:main',
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A GeoSetter-like application for Linux",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pygeosetter",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
