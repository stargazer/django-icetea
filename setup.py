try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
	name="django-icetea",
	version="0.1dev",
	author="C. Paschalides",
	author_email="already.late@gmail.com",
	url="http://github.com/stargazer/django-icetea", 
	long_description=open('README.md').read(),
	packages=('icetea', ),
	install_requires=(
		"Django>=1.3-beta,<=1.3",
        "xlwt",
	),
	zip_safe=True,
)
