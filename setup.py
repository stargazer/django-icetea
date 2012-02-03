try:
    from setuptools import setup
except ImportError:
	from distutils.core import setup

setup(
	name="django-icetea",
	version="0.1dev",
	author="Pambo Paschalides",
	author_email="already.late@gmail.com",
	url="http://github.com/stargazer/django-icetea", 
	long_description=open('README.txt').read(),
	packages=('icetea', ),
	install_requires=(
		"Django>=1.3-beta,<=1.3",
		"xlwt>=0.7.2,<=0.7.2",
	),
	zip_safe=True,
)
