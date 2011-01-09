import sys
import shutil
from os.path import join, dirname, realpath, sep
from os import walk
from glob import glob
from distutils.core import setup
from distutils.extension import Extension

# extract version (simulate doc generation, kivy will be not imported)
import kivy

# extra build commands go in the cmdclass dict {'command-name': CommandClass}
# see tools.packaging.{platform}.build.py for custom build commands for portable packages
# also e.g. we use build_ext command from cython if its installed for c extensions
cmdclass = {}

# add build rules for portable packages to cmdclass
if sys.platform == 'win32':
    from kivy.tools.packaging.win32.build import WindowsPortableBuild
    cmdclass['build_portable'] = WindowsPortableBuild
elif sys.platform == 'darwin':
   from kivy.tools.packaging.osx.build import OSXPortableBuild
   cmdclass['build_portable'] = OSXPortableBuild

from kivy.tools.packaging.factory import FactoryBuild
cmdclass['build_factory'] = FactoryBuild


# extension modules
ext_modules = []

# list all files to compile
import fnmatch
import os

pyx_files = []
kivy_libs_dir = realpath(kivy.kivy_libs_dir)
for root, dirnames, filenames in os.walk(join(dirname(__file__), 'kivy')):
    # ignore lib directory
    if realpath(root).startswith(kivy_libs_dir):
        continue
    for filename in fnmatch.filter(filenames, '*.pyx'):
        pyx_files.append(os.path.join(root, filename))

# check for cython
try:
    have_cython = True
    from Cython.Distutils import build_ext
except:
    have_cython = False

# create .c for every module
if 'sdist' in sys.argv and have_cython:
    from Cython.Compiler.Main import compile
    print 'Generating C files...',
    compile(pyx_files)
    print 'Done !'

#add cython core extension modules if cython is available
if have_cython:
    cmdclass['build_ext'] = build_ext
else:
    pyx_files = ['%s.c' % x[:-4] for x in pyx_files]

if True:
    libraries = []
    include_dirs = []
    extra_link_args = []
    if sys.platform == 'win32':
        libraries.append('opengl32')
    elif sys.platform == 'darwin':
        '''
        # On OSX, gl.h is not in GL/gl.h but OpenGL/gl.h. Cython has no
        # such thing as #ifdef, hence we just copy the file here.
        source = '/System/Library/Frameworks/OpenGL.framework/Versions/A/Headers/gl.h'
        incl = 'build/include/'
        dest = os.path.join(incl, 'GL/')
        try:
            os.makedirs(dest)
        except OSError:
            # Already exists, so don't care
            pass
        shutil.copy(source, dest)
        include_dirs = [incl]
        '''
        # On OSX, it's not -lGL, but -framework OpenGL...
        extra_link_args = ['-framework', 'OpenGL']
    elif sys.platform.startswith('freebsd'):
        include_dirs += ['/usr/local/include']
        extra_link_args += ['-L', '/usr/local/lib']
    else:
        libraries.append('GLESv2')

    # simple extensions
    for pyx in (x for x in pyx_files if not 'graphics' in x):
        module_name = '.'.join(pyx.split('.')[:-1]).replace(sep, '.')
        ext_modules.append(Extension(module_name, [pyx]))

    # opengl aware modules
    for pyx in (x for x in pyx_files if 'graphics' in x):
        module_name = '.'.join(pyx.split('.')[:-1]).replace(sep, '.')
        ext_modules.append(Extension(
            module_name, [pyx],
            libraries=libraries,
            include_dirs=include_dirs,
            extra_link_args=extra_link_args
        ))


    #poly2try extension
    """
    ext_modules.append(Extension('kivy.c_ext.p2t', [
     'kivy/lib/poly2tri/src/p2t.pyx',
     'kivy/lib/poly2tri/poly2tri/common/shapes.cc',
     'kivy/lib/poly2tri/poly2tri/sweep/advancing_front.cc',
     'kivy/lib/poly2tri/poly2tri/sweep/cdt.cc',
     'kivy/lib/poly2tri/poly2tri/sweep/sweep.cc',
     'kivy/lib/poly2tri/poly2tri/sweep/sweep_context.cc'
    ], language="c++"))
    """

#setup datafiles to be included in the disytibution, liek examples...
#extracts all examples files except sandbox
data_file_prefix = 'share/kivy-'
examples = {}
examples_allowed_ext = ('readme', 'py', 'wav', 'png', 'jpg', 'svg',
                        'avi', 'gif', 'txt', 'ttf', 'obj', 'mtl')
for root, subFolders, files in walk('examples'):
    if 'sandbox' in root:
        continue
    for file in files:
        ext = file.split('.')[-1].lower()
        if ext not in examples_allowed_ext:
            continue
        filename = join(root, file)
        directory = '%s%s' % (data_file_prefix, dirname(filename))
        if not directory in examples:
            examples[directory] = []
        examples[directory].append(filename)



# setup !
setup(
    name='Kivy',
    version=kivy.__version__,
    author='Kivy Crew',
    author_email='kivy-dev@googlegroups.com',
    url='http://kivy.org/',
    license='LGPL',
    description='A framework for making accelerated multitouch UI',
    ext_modules=ext_modules,
    cmdclass=cmdclass,
    test_suite='nose.collector',
    packages=[
        'kivy',
        'kivy.core',
        'kivy.core.audio',
        'kivy.core.camera',
        'kivy.core.clipboard',
        'kivy.core.image',
        'kivy.core.gl',
        'kivy.core.spelling',
        'kivy.core.svg',
        'kivy.core.text',
        'kivy.core.video',
        'kivy.core.window',
        'kivy.graphics',
        'kivy.input',
        'kivy.input.postproc',
        'kivy.input.providers',
        'kivy.lib',
        'kivy.lib.osc',
        'kivy.modules',
        'kivy.tools',
        'kivy.tools.packaging',
        'kivy.tools.packaging.win32',
        'kivy.tools.packaging.osx',
        'kivy.uix',
    ],
    package_dir={'kivy': 'kivy'},
    package_data={'kivy': [
        'data/*.kv',
        'data/fonts/*.ttf',
        'data/images/*.png',
        'data/glsl/*.png',
        'data/glsl/*.vs',
        'data/glsl/*.fs',
        'tools/packaging/README.txt',
        'tools/packaging/win32/kivy.bat',
        'tools/packaging/win32/README.txt',
        'tools/packaging/osx/kivy.sh',]
    },
    data_files=examples.items(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: MacOS X',
        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: BSD :: FreeBSD',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Artistic Software',
        'Topic :: Games/Entertainment',
        'Topic :: Multimedia :: Graphics :: 3D Rendering',
        'Topic :: Multimedia :: Graphics :: Capture :: Digital Camera',
        'Topic :: Multimedia :: Graphics :: Presentation',
        'Topic :: Multimedia :: Graphics :: Viewers',
        'Topic :: Multimedia :: Sound/Audio :: Players :: MP3',
        'Topic :: Multimedia :: Video :: Display',
        'Topic :: Scientific/Engineering :: Human Machine Interfaces',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: User Interfaces',
    ]
)
