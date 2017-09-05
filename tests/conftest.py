import os


def pytest_configure():
    from django.conf import settings

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.sample_project.sample.settings")

    try:
        import django
        django.setup()
    except AttributeError:
        pass
