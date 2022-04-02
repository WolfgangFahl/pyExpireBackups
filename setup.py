import pathlib
import os
from expirebackups.version import Version
from setuptools import setup
from collections import OrderedDict

try:
    long_description = ""
    with open('README.md', encoding='utf-8') as f:
        long_description = f.read()

except:
    print('Curr dir:', os.getcwd())
    long_description = open('../../README.md').read()
here = pathlib.Path(__file__).parent.resolve()
requirements = (here / 'requirements.txt').read_text(encoding='utf-8').split("\n")

setup(name=Version.name,
      version=Version.version,
      description=Version.description,
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='http://wiki.bitplan.com/index.php/pyExpireBackups',
      download_url='https://github.com/WolfgangFahl/pyExpireBackups',
      author='Wolfgang Fahl',
      author_email='wf@bitplan.com',
      license='Apache',
      project_urls=OrderedDict(
        (
            ("Code", "https://github.com/WolfgangFahl/pyExpireBackups"),
            ("Issue tracker", "https://github.com/WolfgangFahl/pyExpireBackups/issues"),
        )
      ),
      classifiers=[
            'Programming Language :: Python',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10'
      ],
      packages=['expirebackups'],
      install_requires=requirements,
      entry_points={
         'console_scripts': [
             'expireBackups = expirebackups.expire:main',
      ],
    },
      zip_safe=False)
