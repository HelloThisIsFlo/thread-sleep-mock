from setuptools import find_packages, setup

setup(
    name='thread-sleep-mock',
    version='1.0.0',
    description='Control time: Mock `time.sleep(...)` in Threads, fast-forward in time, perform your assertions at specific points in the future.',
    long_description='See: https://github.com/FlorianKempenich/thread-sleep-mock',
    keywords='threading threads test tdd clean-code asynchronous testing',
    classifiers=[
        'Environment :: Console',
        'Framework :: Pytest',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Utilities',
        'Topic :: Software Development :: Testing'
    ],
    url='https://github.com/FlorianKempenich/thread-sleep-mock',
    author='Florian Kempenich',
    author_email='Flori@nKempenich.com',
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    license='MIT',
    install_requires=[],
    include_package_data=True
)
