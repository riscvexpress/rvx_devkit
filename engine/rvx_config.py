# ****************************************************************************
# ****************************************************************************
# Copyright SoC Design Research Group, All rights reserved.
# Electronics and Telecommunications Research Institute (ETRI)
##
# THESE DOCUMENTS CONTAIN CONFIDENTIAL INFORMATION AND KNOWLEDGE
# WHICH IS THE PROPERTY OF ETRI. NO PART OF THIS PUBLICATION IS
# TO BE USED FOR ANY OTHER PURPOSE, AND THESE ARE NOT TO BE
# REPRODUCED, COPIED, DISCLOSED, TRANSMITTED, STORED IN A RETRIEVAL
# SYSTEM OR TRANSLATED INTO ANY OTHER HUMAN OR COMPUTER LANGUAGE,
# IN ANY FORM, BY ANY MEANS, IN WHOLE OR IN PART, WITHOUT THE
# COMPLETE PRIOR WRITTEN PERMISSION OF ETRI.
# ****************************************************************************
# 2020-02-17
# Kyuseung Han (han@etri.re.kr)
# ****************************************************************************
# ****************************************************************************

import os
import re
from pathlib import Path

from config_file_manager import *


class RvxToolConfig(ConfigFileManager):
    def __init__(self, file_path: Path):
        super().__init__('rvx_tool_config', file_path)
        self.allowed_set = frozenset(('rtl_simulator', 'implements_fpga_in_terminal', 'runs_ocd_in_terminal',
                                     'connects_ocd_in_terminal', 'shows_printf_in_terminal', 'builds_incrementally', 'printf_log_filename'))
        if not self.check(self.allowed_set, matches_exactly=True):
            self.clear()
            assert self.check(self.allowed_set, matches_exactly=True)

    def clear(self):
        super().clear()
        self.set_attr('rtl_simulator', 'xsim')
        if run_shell_cmd('xmsim -version', self.file_path.parent, prints_when_error=False, asserts_when_error=False).returncode == 0:
            self.set_attr('rtl_simulator', 'xcelium')
        elif run_shell_cmd('ncsim -version', self.file_path.parent, prints_when_error=False, asserts_when_error=False).returncode == 0:
            self.set_attr('rtl_simulator', 'ncsim')
        elif run_shell_cmd('vsim -version', self.file_path.parent, prints_when_error=False, asserts_when_error=False).returncode == 0:
            self.set_attr('rtl_simulator', 'questasim')
        self.set_attr('implements_fpga_in_terminal', False)
        self.set_attr('runs_ocd_in_terminal', True)
        self.set_attr('connects_ocd_in_terminal', True)
        self.set_attr('shows_printf_in_terminal', True)
        self.set_attr('builds_incrementally', True)
        self.set_attr('printf_log_filename', None)


class RvxConfig():

    @property
    def tool_config_path(self):
        return self.home_path / '.rvx_tool_config'

    @property
    def ocd_binary_file(self):
        return self.binary_path / 'ocd' / ('openocd_rvp' if is_linux else 'openocd_rvp.exe')

    def __init__(self, home_path: Path = None):
        self.home_path = home_path.resolve()
        assert ' ' not in str(
            self.home_path), 'space is NOT allowed in home path'
        assert self.home_path.is_dir(), home_path
        self.__read_path_config(self.home_path / 'rvx_config_path.mh')
        self.python3_cmd = RvxConfig.__read_python3_cmd(self.home_path / 'rvx_config_python.mh')
        self.tool_config = RvxToolConfig(self.tool_config_path)

    def __read_path_config(self, config_file: Path):
        assert config_file.is_file(), config_file
        var_dict = {'RVX_RELEASE_HOME': self.home_path.as_posix()}
        for line in config_file.read_text(encoding='utf8').splitlines():
            match = re.match(r'^\s*(\w+_HOME)\s*(\??=)\s*(\S+)\s*$', line)
            if not match:
                continue
            name, assign, value = match.groups()
            value = re.sub(r'\$\{(\w+)\}', lambda x: var_dict[x.group(1)], value)
            if assign == '?=' and os.environ.get(name):
                value = os.environ[name]
            var_dict[name] = value
            path = Path(value)
            attr_name = re.sub(r'^RVX_|(_HW)?_HOME$', '', name).lower() + '_path'
            setattr(self, attr_name, path if path.is_dir() else None)
        assert self.devkit_path, config_file

    @staticmethod
    def __read_python3_cmd(config_file: Path):
        assert config_file.is_file(), config_file
        match = re.search(r'^export\s+PYTHON3_CMD\s*:?=\s*(\S+)\s*$', config_file.read_text(encoding='utf8'), re.MULTILINE)
        assert match, config_file
        python3_cmd = match.group(1)
        assert Path(python3_cmd).is_file(), python3_cmd
        return python3_cmd

    def __getattr__(self, name: str):
        if name in self.__dict__.keys():
            result = self.__dict__[name]
        elif name in self.tool_config.keys():
            result = self.tool_config.get_attr(name)
        else:
            assert 0, name
        return result
