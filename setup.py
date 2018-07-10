import io

from setuptools import find_packages, setup


def read(filename):
    with io.open(filename, encoding='utf-8') as f:
        return f.read()


setup(
    name='djangorestframework-guardian',
    version='0.1.0',
    author='Ryan P Kilby',
    url='https://github.com/rpkilby/django-rest-framework-guardian',
    description='django-guardian support for Django REST Framework',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    license='BSD',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    include_package_data=True,
    install_requires=['django', 'djangorestframework', 'django-guardian'],
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
