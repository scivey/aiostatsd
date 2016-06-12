from distutils.core import setup

setup(
    name='aiostatsd',
    version='1.0.0',
    description="An asyncio statsd client",
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3'
    ],
    author='Scott Ivey',
    author_email='scott.ivey@gmail.com',
    license='MIT',
    install_requires=[
        "cython>=0.24.0",
        "cystatsd>=1.0.2"
    ],
    packages=[
        'aiostatsd'
    ],
    provides=['aiostatsd']
)

