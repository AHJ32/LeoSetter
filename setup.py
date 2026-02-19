from setuptools import setup, find_packages

setup(
    name="leosetter",
    version="0.1.0",
    packages=find_packages(),
    py_modules=["run_mvp"],  # include top-level entry module
    install_requires=[
        'PyQt5>=5.15.0',
        'PyQtWebEngine>=5.15.0',
    ],
    entry_points={
        'console_scripts': [
            'leosetter=run_mvp:main',
        ],
    },
    author="Retro",
    author_email="jihadanamulhaque9@gmail.com",
    description="LeoSetter - a modern photo metadata editor (GeoSetter-style) for Linux and Windows",
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/AHJ32/Geo-Setter-Linux-Clone",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: X11 Applications :: Qt",
        "Topic :: Multimedia :: Graphics",
    ],
    python_requires='>=3.8',
)
