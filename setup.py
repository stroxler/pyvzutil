from setuptools import setup


def readme():
    with open('README') as f:
        return f.read()


setup(name='pyvzutil',
      version='0.0.12',
      description='Utilities for working with openvz clusters',
      long_description=readme(),
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 2.7',
      ],
      keywords='cluster ssh openvz scp',
      url='http://github.com/stroxler/pyvzutil',
      author='Steven Troxler',
      author_email='steven.troxler@gmail.com',
      license='MIT',
      packages=['pyvzutil'],
      install_requires=[
          'sh',
      ],
      include_package_data=True,
      zip_safe=False)
