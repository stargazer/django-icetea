try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="django-icetea",
    packages=('icetea',),
    version="0.5.5",
    description="REST API Framework",
    author="C. Paschalides",
    author_email="already.late@gmail.com",
    license="WTFPL",
    url="http://github.com/stargazer/django-icetea",
    keywords=("rest", "restful", "api", "crud"),
    install_requires=(
        "Django>=1.6,<1.8",
        "xlwt",
    ),
    zip_safe=False,
    classifiers=(
        "Programming Language :: Python",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: Freely Distributable",
        "Development Status :: 4 - Beta",
    ),
)
