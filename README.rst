django-icetea
==================
``django-icetea`` is a package built on top of ``Django``, which lays the
foundation for creating APIs. 

It is heavily influenced by ``django-piston`` and
``piston-perfect``. ``piston-perfect`` was built on top of ``django-piston``,
and the combination of the two, was actually a very stable package. However,
the code used a lot of ugly hacks and monkey-patching, which made it quite
incomprehensible, and not very easy to tweak.

For these reasons, I've decided to build ``django-icetea``, which basically
throws away all the extras of ``django-piston`` and borrows ideas from
``piston-perfect``, in order to create, a clean, maintainable and rock-solid
API package.


