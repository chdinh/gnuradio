#
# Copyright 2013-2014,2017-2019 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
#
""" Module to add new blocks """

from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import os
import re
import logging

from ..tools import render_template, append_re_line_sequence, CMakeFileEditor, CPPFileEditor, code_generator
from ..templates import Templates
from .base import ModTool, ModToolException
from gnuradio.bindtool import BindingGenerator
from gnuradio import gr

logger = logging.getLogger(__name__)


class ModToolAdd(ModTool):
    """ Add block to the out-of-tree module. """
    name = 'add'
    description = 'Add new block into a module.'
    block_types = ('sink', 'source', 'sync', 'decimator', 'interpolator',
                    'general', 'tagged_stream', 'hier', 'noblock')
    language_candidates = ('cpp', 'python', 'c++')

    def __init__(self, blockname=None, block_type=None, lang=None, copyright=None,
                 license_file=None, argument_list="", add_python_qa=False,
                 add_cpp_qa=False, skip_cmakefiles=False, **kwargs):
        ModTool.__init__(self, blockname, **kwargs)
        self.info['blocktype'] = block_type
        self.info['lang'] = lang
        self.license_file = license_file
        self.info['copyrightholder'] = copyright
        self.info['arglist'] = argument_list
        self.add_py_qa = add_python_qa
        self.add_cc_qa = add_cpp_qa
        self.skip_cmakefiles = skip_cmakefiles

    def validate(self):
        """ Validates the arguments """
        ModTool._validate(self)
        if self.info['blocktype'] is None:
            raise ModToolException('Blocktype not specified.')
        if self.info['blocktype'] not in self.block_types:
            raise ModToolException('Invalid blocktype')
        if self.info['lang'] is None:
            raise ModToolException('Programming language not specified.')
        if self.info['lang'] not in self.language_candidates:
            raise ModToolException('Invalid programming language.')
        if self.info['blocktype'] == 'tagged_stream' and self.info['lang'] == 'python':
            raise ModToolException('Tagged Stream Blocks for Python currently unsupported')            
        if self.info['blockname'] is None:
            raise ModToolException('Blockname not specified.')
        if not re.match('^[a-zA-Z0-9_]+$', self.info['blockname']):
            raise ModToolException('Invalid block name.')
        if not isinstance(self.add_py_qa, bool):
            raise ModToolException('Expected a boolean value for add_python_qa.')
        if not isinstance(self.add_cc_qa, bool):
            raise ModToolException('Expected a boolean value for add_cpp_qa.')
        if not isinstance(self.skip_cmakefiles, bool):
            raise ModToolException('Expected a boolean value for skip_cmakefiles.')

    def assign(self):
        if self.info['lang'] == 'c++':
            self.info['lang'] = 'cpp'
        if ((self.skip_subdirs['lib'] and self.info['lang'] == 'cpp')
                or (self.skip_subdirs['python'] and self.info['lang'] == 'python')):
            raise ModToolException('Missing or skipping relevant subdir.')
        self.info['fullblockname'] = self.info['modname'] + '_' + self.info['blockname']
        if not self.license_file:
            if self.info['copyrightholder'] is None:
                self.info['copyrightholder'] = '<+YOU OR YOUR COMPANY+>'
        self.info['license'] = self.setup_choose_license()
        if (self.info['blocktype'] in ('noblock') or self.skip_subdirs['python']):
            self.add_py_qa = False
        if not self.info['lang'] == 'cpp':
            self.add_cc_qa = False
        if self.info['version'] == 'autofoo' and not self.skip_cmakefiles:
            self.skip_cmakefiles = True

    def setup_choose_license(self):
        """ Select a license by the following rules, in this order:
        1) The contents of the file given by --license-file
        2) The contents of the file LICENSE or LICENCE in the modules
           top directory
        3) The default license. """
        if self.license_file is not None \
            and os.path.isfile(self.license_file):
            with open(self.license_file) as f:
                return f.read()
        elif os.path.isfile('LICENSE'):
            with open('LICENSE') as f:
                return f.read()
        elif os.path.isfile('LICENCE'):
            with open('LICENCE') as f:
                return f.read()
        elif self.info['is_component']:
            return Templates['grlicense']
        else:
            return Templates['defaultlicense'].format(**self.info)

    def _write_tpl(self, tpl, path, fname):
        """ Shorthand for writing a substituted template to a file"""
        path_to_file = os.path.join(path, fname)
        logger.info("Adding file '{}'...".format(path_to_file))
        with open(path_to_file, 'w') as f:
            f.write(render_template(tpl, **self.info))
        self.scm.add_files((path_to_file,))

    def run(self):
        """ Go, go, go. """

        # Some validation covered by the CLI - validate all parameters here
        self.validate()
        self.assign()

        has_pybind = (
                self.info['lang'] == 'cpp'
                and not self.skip_subdirs['python']
        )
        has_grc = False
        if self.info['lang'] == 'cpp':
            self._run_lib()
            has_grc = has_pybind
        else: # Python
            self._run_python()
            if self.info['blocktype'] != 'noblock':
                has_grc = True
        if has_pybind:
            self._run_pybind()
        if self.add_py_qa:
            self._run_python_qa()
        if has_grc and not self.skip_subdirs['grc']:
            self._run_grc()

    def _run_cc_qa(self):
        " Add C++ QA files for 3.7 API if intructed from _run_lib"
        fname_qa_h  = 'qa_{}.h'.format(self.info['blockname'])
        fname_qa_cc = 'qa_{}.cc'.format(self.info['blockname'])
        self._write_tpl('qa_cpp', 'lib', fname_qa_cc)
        self._write_tpl('qa_h',   'lib', fname_qa_h)
        if self.skip_cmakefiles:
            return
        try:
            append_re_line_sequence(self._file['cmlib'],
                                    r'list\(APPEND test_{}_sources.*\n'.format(self.info['modname']),
                                    'qa_{}.cc'.format(self.info['blockname']))
            append_re_line_sequence(self._file['qalib'],
                                    '#include.*\n',
                                    '#include "{}"'.format(fname_qa_h))
            append_re_line_sequence(self._file['qalib'],
                                    '(addTest.*suite.*\n|new CppUnit.*TestSuite.*\n)',
                                    '  s->addTest(gr::{}::qa_{}::suite());'.format(self.info['modname'],
                                                                                   self.info['blockname'])
                                    )
            self.scm.mark_files_updated((self._file['qalib'],))
        except IOError:
            logger.warning("Can't add C++ QA files.")

    def _run_cc_qa_boostutf(self):
        " Add C++ QA files for 3.8 API if intructed from _run_lib"
        fname_qa_cc = 'qa_{}.cc'.format(self.info['blockname'])
        self._write_tpl('qa_cpp_boostutf', 'lib', fname_qa_cc)
        if self.skip_cmakefiles:
            return
        try:
            append_re_line_sequence(self._file['cmlib'],
                                   r'list\(APPEND test_{}_sources.*\n'.format(self.info['modname']),
                                    'qa_{}.cc'.format(self.info['blockname']))
            self.scm.mark_files_updated((self._file['cmlib'],))
        except IOError:
            logger.warning("Can't add C++ QA files.")

    def _run_lib(self):
        """ Do everything that needs doing in the subdir 'lib' and 'include'.
        - add .cc and .h files
        - include them into CMakeLists.txt
        - check if C++ QA code is req'd
        - if yes, create qa_*.{cc,h} and add them to CMakeLists.txt
        """
        fname_cc = None
        fname_h = None
        if self.info['version'] in ('37', '38'):
            fname_h = self.info['blockname'] + '.h'
            fname_cc = self.info['blockname'] + '.cc'
            if self.info['blocktype'] in ('source', 'sink', 'sync', 'decimator',
                                           'interpolator', 'general', 'hier', 'tagged_stream'):
                fname_cc = self.info['blockname'] + '_impl.cc'
                self._write_tpl('block_impl_h',   'lib', self.info['blockname'] + '_impl.h')
            self._write_tpl('block_impl_cpp', 'lib', fname_cc)
            self._write_tpl('block_def_h',    self.info['includedir'], fname_h)
        else: # Pre-3.7 or autotools
            fname_h  = self.info['fullblockname'] + '.h'
            fname_cc = self.info['fullblockname'] + '.cc'
            self._write_tpl('block_h36',   self.info['includedir'], fname_h)
            self._write_tpl('block_cpp36', 'lib',                    fname_cc)
        if self.add_cc_qa:
            if self.info['version'] == '38':
                self._run_cc_qa_boostutf()
            elif self.info['version'] == '37':
                self._run_cc_qa()
            elif self.info['version'] == '36':
                logger.warning("Warning: C++ QA files not supported for 3.6-style OOTs.")
            elif self.info['version'] == 'autofoo':
                logger.warning("Warning: C++ QA files not supported for autotools.")
        if not self.skip_cmakefiles:
            ed = CMakeFileEditor(self._file['cmlib'])
            cmake_list_var = '[a-z]*_?' + self.info['modname'] + '_sources'
            if not ed.append_value('list', fname_cc, to_ignore_start='APPEND ' + cmake_list_var):
                ed.append_value('add_library', fname_cc)
            ed.write()
            ed = CMakeFileEditor(self._file['cminclude'])
            ed.append_value('install', fname_h, to_ignore_end='DESTINATION[^()]+')
            ed.write()
            self.scm.mark_files_updated((self._file['cminclude'], self._file['cmlib']))

    def _run_pybind(self):
        """ Do everything that needs doing in the python bindings subdir.
        - add blockname_python.cc 
        - add reference and call to bind_blockname()
        - include them into CMakeLists.txt
        """

        # Generate bindings cc file
        fname_cc = self.info['blockname'] + '_python.cc'

        # Update python_bindings.cc
        ed = CPPFileEditor(self._file['ccpybind'])
        ed.append_value('// BINDING_FUNCTION_PROTOTYPES(', '// ) END BINDING_FUNCTION_PROTOTYPES', 
            'void bind_' + self.info['blockname'] + '(py::module& m);')
        ed.append_value('// BINDING_FUNCTION_CALLS(', '// ) END BINDING_FUNCTION_CALLS', 
            'bind_' + self.info['blockname'] + '(m);')
        ed.write()

        self.scm.mark_files_updated((self._file['ccpybind']))

        bg = BindingGenerator(prefix=gr.prefix(), namespace=['gr',self.info['modname']], prefix_include_root=self.info['modname'])
        block_base = ""
        if self.info['blocktype'] in ('source', 'sink', 'sync', 'decimator',
                                        'interpolator', 'general', 'hier', 'tagged_stream'):
            block_base = code_generator.GRTYPELIST[self.info['blocktype']]

        header_info = {
            "module_name": self.info['modname'],
            "namespace": {
                "name": "::".join(['gr', self.info['modname']]),
                "enums": [],
                "variables": [],
                "classes": [
                    {
                        "name": self.info['blockname'],
                        "member_functions": [
                            {
                                "name": "make",
                                "return_type": "::".join(("gr",self.info['modname'],self.info['blockname'],"sptr")),
                                "has_static": "1",
                                "arguments": []
                            }
                        ],
                        "bases": [
                            "::",
                            "gr",
                            block_base
                        ],
                        "constructors": [
                            {
                                "name": self.info['blockname'],
                                "arguments": []
                            }
                        ]
                    }
                ],
                "free_functions": [],
                "namespaces": []
            }
        }
        # def gen_pybind_cc(self, header_info, base_name):
        cc_txt = bg.gen_pybind_cc(header_info,self.info['blockname'])
        path_to_file = os.path.join('python','bindings', fname_cc)
        logger.info("Adding file '{}'...".format(path_to_file))
        with open(path_to_file, 'w') as f:
            f.write(cc_txt)
        self.scm.add_files((path_to_file,))

        if not self.skip_cmakefiles:
            ed = CMakeFileEditor(self._file['cmpybind'])
            cmake_list_var = '[a-z]*_?' + self.info['modname']
            ed.append_value('pybind11_add_module', fname_cc, to_ignore_start=cmake_list_var, to_ignore_end='python_bindings.cc')
            ed.write()
            self.scm.mark_files_updated((self._file['cmpybind']))


    def _run_python_qa(self):
        """ Do everything that needs doing in the subdir 'python' to add
        QA code.
        - add .py files
        - include in CMakeLists.txt
        """
        fname_py_qa = 'qa_' + self.info['blockname'] + '.py'
        self._write_tpl('qa_python', self.info['pydir'], fname_py_qa)
        os.chmod(os.path.join(self.info['pydir'], fname_py_qa), 0o755)
        self.scm.mark_files_updated((os.path.join(self.info['pydir'], fname_py_qa),))
        if self.skip_cmakefiles or CMakeFileEditor(self._file['cmpython']).check_for_glob('qa_*.py'):
            return
        logger.info("Editing {}/CMakeLists.txt...".format(self.info['pydir']))
        with open(self._file['cmpython'], 'a') as f:
            f.write(
                'GR_ADD_TEST(qa_%s ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/%s)\n' % \
                (self.info['blockname'], fname_py_qa))
        self.scm.mark_files_updated((self._file['cmpython'],))

    def _run_python(self):
        """ Do everything that needs doing in the subdir 'python' to add
        a Python block.
        - add .py file
        - include in CMakeLists.txt
        - include in __init__.py
        """
        fname_py = self.info['blockname'] + '.py'
        self._write_tpl('block_python', self.info['pydir'], fname_py)
        append_re_line_sequence(self._file['pyinit'],
                                '(^from.*import.*\n|# import any pure.*\n)',
                                'from .{} import {}'.format(self.info['blockname'], self.info['blockname']))
        self.scm.mark_files_updated((self._file['pyinit'],))
        if self.skip_cmakefiles:
            return
        ed = CMakeFileEditor(self._file['cmpython'])
        ed.append_value('GR_PYTHON_INSTALL', fname_py, to_ignore_end='DESTINATION[^()]+')
        ed.write()
        self.scm.mark_files_updated((self._file['cmpython'],))

    def _run_grc(self):
        """ Do everything that needs doing in the subdir 'grc' to add
        a GRC bindings YAML file.
        - add .yml file
        - include in CMakeLists.txt
        """
        fname_grc = self.info['fullblockname'] + '.block.yml'
        self._write_tpl('grc_yml', 'grc', fname_grc)
        ed = CMakeFileEditor(self._file['cmgrc'], '\n    ')
        if self.skip_cmakefiles or ed.check_for_glob('*.yml'):
            return
        logger.info("Editing grc/CMakeLists.txt...")
        ed.append_value('install', fname_grc, to_ignore_end='DESTINATION[^()]+')
        ed.write()
        self.scm.mark_files_updated((self._file['cmgrc'],))
