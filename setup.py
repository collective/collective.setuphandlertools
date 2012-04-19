from setuptools import setup, find_packages
import os

version = '1.0b4'

setup(name='collective.setuphandlertools',
      version=version,
      description="Tools for setting up a Plone site.",
      long_description=open("README.txt").read() + "\n\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        ],
      keywords='plone zope setup',
      author='Johannes Raggam',
      author_email='raggam-nl@adm.at',
      url='http://github.com/collective/collective.setuphandlertools',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
          'Plone',
          'Products.ATContentTypes',
          'Products.CMFCore',
          'Products.PortalTransforms',
      ],
      )
