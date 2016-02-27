from setuptools import setup, find_packages
setup(
    name = "PythonCypher",
    version = "0.1",
    packages = find_packages(),
    scripts = ['python_cypher/cypher_tokenizer.py', 'python_cypher/cypher_parser.py', 'python_cypher/python_cypher.py'],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = ['docutils>=0.3'],

    package_data = {
    },
    # metadata for upload to PyPI
    author = "Zachary Ernst",
    author_email = "zac.ernst@gmail.com",
    description = "Cypher query language for Python",
    license = "GPL 2",
    keywords = "cypher neo4j ",
    url = "",   # project home page, if any
)
