Test Suite for django-icetea
-----------------------------

Build a simple Django project found under the 
``project`` folder, and runs some tests against it, in order to validate the behavior of ``django-icetea``.

The procedure is very simple:

1. ``python boodstrap.py -d`` to create the necessary folder structure
2. ``bin/buildout`` to pull all the dependencies of this small django project and build the scripts
3. ``bin/test`` to run the test suite
