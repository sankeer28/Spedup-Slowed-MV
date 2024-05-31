from setuptools import setup, find_packages
setup(
name='Spedup-Slowed-MV',
version='0.1.0',
author='sankeer',
author_email='sankeer28@gmail.com',
description='A Python script that automates the creation of nightcore-style/sped-up videos or slowed-down videos by combining a wallpaper with audio extracted from URLs from supported websites like YouTube, YouTube music, and Soundcloud.',
packages=find_packages(),
classifiers=[
'Programming Language :: Python :: 3',
'License :: OSI Approved :: MIT License',
'Operating System :: OS Independent',
],
python_requires='>=3.11',
)

from distutils.core import setup
setup(
  name = 'Spedup-Slowed-MV',         # How you named your package folder (MyLib)
  packages = ['Spedup-Slowed-MV'],   # Chose the same as "name"
  version = '0.1',      # Start with a small number and increase it with every change you make
  license='MIT',        # Chose a license from here: https://help.github.com/articles/licensing-a-repository
  description = 'A Python script that automates the creation of nightcore-style/sped-up videos or slowed-down videos by combining a wallpaper with audio extracted from URLs from supported websites like YouTube, YouTube music, and Soundcloud.',   # Give a short description about your library
  author = 'Sankeer',                   # Type in your name
  author_email = 'sankeer28@gmail.com',      # Type in your E-Mail
  url = 'https://github.com/sankeer28/Spedup-Slowed-MV',   # Provide either the link to your github or to your website
  download_url = 'https://github.com/sankeer28/Spedup-Slowed-MV',    # I explain this later on
  keywords = ['music'],   # Keywords that define your package best
  install_requires=[            # I get to this in a second
            'Brotli',
            'certifi',
            'charset-normalizer',
            'idna',
            'mutagen',
            'pycryptodomex',
            'requests',
            'urllib3'
            'websockets',
            'yt-dlp'
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers',      # Define that your audience are developers
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',   # Again, pick a license
    'Programming Language :: Python :: 3.12',
    'Programming Language :: Python :: 3.10',
  ],
)
