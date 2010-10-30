#!/usr/bin/env python

from distutils.core import setup

setup(
      name='Minecraft',
      version='0.7',
      description='Minecraft data utilities'
      author='David Walker'
      author_email='d0sboots@gmail.com',
      url='http://github.com/d0sboots/Minecraft'
      license = open("LICENSE.txt").read(),
      long_description = open("README.txt").read(),
      py_modules = ['minecraft']
     )
