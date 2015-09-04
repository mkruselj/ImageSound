from distutils.core import setup
import py2exe, sys, os, skimage, PIL, numpy, scipy, pyaudio

sys.argv.append('py2exe')

setup(
    options = {
                    'py2exe': {
                            'bundle_files': 3,
                            'optimize': 2,
                            #'compressed': True,
                            'includes': ['pyaudio', 'scipy', 'numpy', 'skimage', 'PIL', 'difflib', 'locale', 'inspect', 'skimage._shared', 'skimage._shared.geometry', 'scipy.special._ufuncs_cxx', 'scipy.linalg.cython_blas', 'scipy.linalg.cython_lapack', 'scipy.integrate', 'scipy.sparse.csgraph._validation'],
                            'excludes': ['pkg_resources','doctest', 'pdb', 'inspect', 'calendar', 'optparse', 'jsonschema', 'tornado', 'setuptools', 'distutils', 'matplotlib']
                    }
               },
    windows = [{'script': 'ImageSound.py'}],
    data_files = [('images',['images/author.png'])]
)