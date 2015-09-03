dev-install:
	python setup.py develop

install:
	python setup.py install

clean:
	rm -rf dist

package: clean
	python setup.py sdist

# before this works, you have to register a package. You do
# that by typing python setup.py register. You only need to do this
# once.

pypi: package
	 twine upload dist/pyvzutil-0.0.2.tar.gz
