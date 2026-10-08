## ****************************************************************************
## ****************************************************************************
## Copyright SoC Design Research Group, All rights reserved.    
## Electronics and Telecommunications Research Institute (ETRI)
##
## THESE DOCUMENTS CONTAIN CONFIDENTIAL INFORMATION AND KNOWLEDGE 
## WHICH IS THE PROPERTY OF ETRI. NO PART OF THIS PUBLICATION IS 
## TO BE USED FOR ANY OTHER PURPOSE, AND THESE ARE NOT TO BE 
## REPRODUCED, COPIED, DISCLOSED, TRANSMITTED, STORED IN A RETRIEVAL 
## SYSTEM OR TRANSLATED INTO ANY OTHER HUMAN OR COMPUTER LANGUAGE, 
## IN ANY FORM, BY ANY MEANS, IN WHOLE OR IN PART, WITHOUT THE 
## COMPLETE PRIOR WRITTEN PERMISSION OF ETRI.
## ****************************************************************************
## 2019-09-24
## Kyuseung Han (han@etri.re.kr)
## ****************************************************************************
## ****************************************************************************

import argparse
import os
import telnetlib
import time
import platform
import datetime

from itertools import chain
from xml.etree.ElementTree import *

from rvx_engine_util import *
from rvx_devkit import *
from rvx_ila_env import *
from rvx_imp_class import *

import import_util
from gather_files import *
from configure_template import *
from generate_copyright import *
from simulate_rtl import *

# local

# remote

#######################################################################################

class RvxWorkspace():
  def __init__(self, devkit=None, workspace_path:Path=None, platform_name:str=None):
    assert devkit
    assert workspace_path
    self.devkit = devkit
    self.workspace_path = workspace_path
    assert self.workspace_path.absolute(), self.workspace_path
    self.workspace_path = self.workspace_path.resolve()
    self.imp_class = RvxImpClass()
    if self.devkit.get_imp_class_list_common_file.is_file():
      self.imp_class.import_xml(self.devkit.get_imp_class_list_common_file)
      for imp_class_xml in self._get_imp_class_info_path().glob('*/*.xml'):
        self.imp_class.import_xml(imp_class_xml)
      if platform_name:
        for imp_class_xml in sorted(self._get_platform_imp_class_info_path(platform_name).glob('*/*.xml')):
          self.imp_class.import_xml(imp_class_xml)
        
  @property
  def config(self):
    return self.devkit.config
  
  @property
  def devkit_path(self):
    return self.config.devkit_path

  def _get_platform_base_path(self):
    return self.workspace_path
  
  def _get_platform_path(self, platform_name:str):
    return self._get_platform_base_path() / platform_name

  def _get_platform_xml(self, platform_name:str):
    return self._get_platform_path(platform_name) / f'{platform_name}.xml'
  
  def _get_platform_freeze_path(self, platform_name:str):
    return self._get_platform_path(platform_name) / 'freeze'
  
  def _get_platform_freeze_xml_path(self, platform_name:str):
    return self._get_platform_freeze_path(platform_name) / f'{platform_name}.xml'

  def _get_app_base_path(self, platform_name:str):
    return self._get_platform_path(platform_name) /'app'

  def _get_app_path(self, platform_name:str, app_name):
    return self._get_app_base_path(platform_name) / app_name

  def _get_env_file(self, *args):
    return self.devkit.get_devkit_path(*args)

  def _get_imp_path(self, platform_name:str, imp_name:str):
    return self._get_platform_path(platform_name) / imp_name
  
  def _get_imp_class_info_path(self):
    return self.config.imp_class_path

  def _get_platform_imp_class_info_path(self, platform_name:str):
    return (self._get_platform_path(platform_name) / 'user' / 'imp_class').resolve()

  def _get_imp_class_path(self, imp_class_name:str):
    imp_class_xml = self.imp_class.file_dict.get(imp_class_name)
    if imp_class_xml and (imp_class_xml.parent.name==imp_class_name):
      return imp_class_xml.parent.resolve()
    return self._get_imp_class_info_path() / imp_class_name

  def _get_sim_rtl_path(self, platform_name:str):
    return self._get_platform_path(platform_name) / 'sim_rtl'
  
  def _get_rvx_include_path(self, platform_name:str, app_name:str):
    return self._get_app_path(platform_name, app_name) / 'rvx_include'
  
  def _get_user_path(self, platform_name:str):
    return self._get_platform_path(platform_name) / 'user'
  
  def _get_user_template_path(self, platform_name:str):
    return self._get_platform_path(platform_name) / 'user' / 'template'

  def _get_arch_path(self, platform_name:str):
    return self._get_platform_path(platform_name) / 'arch'
  
  def _get_app_config_path(self, platform_name:str, app_name:str):
    app_config_path_old = self._get_app_path(platform_name, app_name) / 'each_app_config.mh'
    app_config_path = self._get_app_path(platform_name, app_name) / 'rvx_each.mh'
    if app_config_path_old.is_file():
      assert not app_config_path.is_file()
      app_config_path = app_config_path_old
    return app_config_path

  @staticmethod
  def _get_build_target(target_imp_class:str, build_mode:str):
    return f'{target_imp_class}.{build_mode}'

  @staticmethod
  def _get_elf_filename(platform_name:str, app_name:str, target_imp_class:str, build_mode:str):
    return f'{app_name}.{platform_name}.elf'

  # relative address
  @staticmethod
  def _get_flash_image_name(platform_name:str, app_name:str, target_imp_class:str, imp_instance_path:Path):
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    return f'{platform_name}.{target_imp_class}.{app_name}.{today}'

  @staticmethod
  def _get_dump_flash_image_script_path(imp_instance_path:Path):
    return imp_instance_path / f'dump_flash_image.tcl'
  
  @staticmethod
  def _get_program_flash_image_script_path(imp_instance_path:Path):
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    return imp_instance_path / f'program_flash_image_wo_rvx.{today}.tcl'
  
  def _get_build_path(self, platform_name:str, app_name:str, target_imp_class:str, build_mode:str):
    build_target = RvxWorkspace._get_build_target(target_imp_class,build_mode)
    build_path = self._get_app_path(platform_name, app_name) / build_target
    return build_path
  
  def _get_elf_path(self, platform_name:str, app_name:str, target_imp_class:str, build_mode:str):
    return self._get_build_path(platform_name, app_name, target_imp_class, build_mode) / RvxWorkspace._get_elf_filename(platform_name, app_name, target_imp_class, build_mode)

  def _get_platform_util_path(self, platform_name:str):
    return self._get_platform_path(platform_name) / 'util'
  
  def _get_memory_info(self, platform_name:str):
    set_memory_path = self._get_arch_path(platform_name) / 'ssw' / 'env'
    set_memory_file = set_memory_path / 'set_memory.mh'
    file_contents = set_memory_file.read_text(encoding='utf8')
    line_list = [x.split('-')[1].split(' ') for x in file_contents.split('\n')]
    return line_list

  def _get_hw_define_dict(self, platform_name:str):
    info = self._get_arch_path(platform_name) / 'rtl' / 'include' / 'hw_info.vh'
    define_list = get_define_list('`define', info)
    define_dict = {}
    for id, value in define_list:
      define_dict[id] = value
    return define_dict

  def __check_status(self, status_list=None):
    assert status_list
    current_status = status_list[-1][2]
    next_status = status_list[0][2]
    for _, path, status in status_list:
      if not path:
        break
      if path.is_file():
        current_status = status
        break
      else:
        next_status = status
    self.devkit.handle_output(f'{current_status} {next_status}')

  def __check_target_imp_class(self, target_imp_class:str):
    imp_class_list = self.info_imp_class_list()
    assert target_imp_class in imp_class_list, f'Undefined HW type \"{target_imp_class}\"'
  
  def __check_fpga_name(self, target_imp_class:str):
    fpga_list = self.info_fpga_list()
    assert target_imp_class in fpga_list, f'Undefined FPGA name \"{target_imp_class}\"'
  
  @staticmethod
  def __clean(target_path, exclude_list):
    for sub in target_path.glob('*'):
      if sub.name not in exclude_list:
        remove(sub)

  def __app_build_makefile(self, platform_name:str, app_name:str, target_imp_class:str, build_mode:str):
    platform_path = self._get_platform_path(platform_name)
    build_path = self._get_build_path(platform_name, app_name, target_imp_class, build_mode)
    template_file = self._get_env_file('makefile', 'Makefile.build.template')
    output_file = build_path / 'Makefile'
    config_list = (('PLATFORM_DIR',str(PurePosixPath(platform_path))), \
                ('PLATFORM_NAME', platform_name), \
                ('APP_NAME', app_name), \
                ('TARGET_IMP_CLASS', target_imp_class), \
                ('BUILD_MODE', build_mode))
    configure_template_file(template_file, output_file, config_list)

  def __get_compile_list_path(self, platform_name:str, app_name:str):
    app_path = self._get_app_path(platform_name,app_name)
    compile_list_file = app_path / 'compile_list'
    return compile_list_file
  
  def app_compile_list(self, platform_name:str, app_name:str):
    compile_list_file = self.__get_compile_list_path(platform_name, app_name)
    if not compile_list_file.is_file():
      line_list = []
      line_list.append('all:./src')
      line_list.append('all:./include')
      line_list.append('all:../../user/api')
      compile_list_file.write_text('\n'.join(line_list), encoding='utf8')

  def app_build_dir(self, platform_name:str, app_name:str, target_imp_class:str, build_mode:str):
    build_path = self._get_build_path(platform_name, app_name, target_imp_class, build_mode)
    build_path.mkdir(exist_ok=True, parents=True)
    self.__app_build_makefile(platform_name,app_name,target_imp_class,build_mode)
    self.devkit.set_gitignore('all', build_path)
  
  def __generate_system_compile_list(self, build_path:Path):
    system_compile_list = self._get_env_file('makefile', 'system_compile_list')
    compile_list = []
    for compile_target_with_var in system_compile_list.read_text(encoding='utf8').split('\n'):
      if compile_target_with_var:
        var, compile_target = compile_target_with_var.split(',')
        if get_makefile_var(var, build_path)=='true':
          compile_list.append(compile_target)
    return compile_list

  def __prepare_app_source(self, platform_name:str, app_name:str, target_imp_class:str, build_mode:str):
    build_path = self._get_build_path(platform_name, app_name, target_imp_class, build_mode)
    new_source_path = build_path / 'src'
    new_include_path = build_path / 'include'
    new_etc_path = build_path / 'etc'
    previous_success_file_path = build_path / 'previous'
    app_config_path = self._get_app_config_path(platform_name, app_name)
    compile_list_path = self.__get_compile_list_path(platform_name, app_name)
    source_suffix_set = frozenset(('.c','.cpp','.S'))
    
    self.app_compile_list(platform_name, app_name)

    if not self.config.builds_incrementally:
      remove_directory(previous_success_file_path)

    compile_list = self.__generate_system_compile_list(build_path)
    compile_list += compile_list_path.read_text(encoding='utf8').split('\n')

    compile_dir_list = []
    for compile_target in compile_list:
      if compile_target:
        allowed_type, dir = compile_target.split(':')
        if allowed_type=='all' or allowed_type==target_imp_class:
          path = Path(dir)
          if not path.is_absolute():
            path = (compile_list_path.parent / path).resolve()
          compile_dir_list.append(path)
    total_file_list = gather_file_list(compile_dir_list, ['.c','.cpp','.S','.h','.a'])
    if app_config_path.is_file():
      total_file_list.append(app_config_path)
    total_filename_set = frozenset([x.name for x in total_file_list])
    previous_file_list = gather_file_list(str(previous_success_file_path), None)
    previous_filename_set = frozenset([x.name for x in previous_file_list])

    def is_already_compiled(path:Path):
      result = True
      if target_file.name not in previous_filename_set:
        result = False
      elif not is_equal_file(target_file, previous_success_file_path / target_file.name):
        result = False
      return result
    
    target_file_list = []
    if len(previous_filename_set)==0:
      is_incremental = False
    elif len(previous_filename_set - total_filename_set) > 0:
      is_incremental = False
    else:
      is_incremental = True  
      for target_file in total_file_list:
        if not is_already_compiled(target_file):
          if target_file.suffix in source_suffix_set:
            target_file_list.append(target_file)
          else:
            is_incremental = False
            break            

    if not is_incremental:
      target_file_list = total_file_list

    if new_source_path.is_dir():
      remove_directory(new_source_path)
    new_source_path.mkdir()
    if new_include_path.is_dir():
      remove_directory(new_include_path)
    new_include_path.mkdir()
    if new_etc_path.is_dir():
      remove_directory(new_etc_path)
    new_etc_path.mkdir()
    for target_file in target_file_list:
      if target_file.suffix=='.h':
        copy_file(target_file, new_include_path)
      elif target_file.suffix in source_suffix_set:
        copy_file(target_file, new_source_path)
      elif target_file==app_config_path:
        copy_file(target_file, new_etc_path)
      elif target_file.suffix=='.a':
        copy_file(target_file, new_etc_path)
      else:
        assert 0, target_file
        
    return is_incremental

  def app_compile(self, platform_name:str, app_name:str, target_imp_class:str, build_mode:str, is_incremental:bool):
    self.check_platform_synthesized_correctly(platform_name)

    build_path = self._get_build_path(platform_name, app_name, target_imp_class, build_mode)
    new_source_path = build_path / 'src'
    new_include_path = build_path / 'include'
    new_etc_path = build_path / 'etc'
    previous_success_file_path = build_path / 'previous'

    target_file_list = []
    target_file_list += new_source_path.glob('*')
    target_file_list += new_include_path.glob('*')
    target_file_list += new_etc_path.glob('*')

    #if is_debug_mode:
    #  print(is_incremental, target_file_list)

    if target_file_list:
      # duplicate header
      new_include_path.mkdir(exist_ok=True)
      for previous_header in previous_success_file_path.glob('*.h'):
        if not (new_include_path / previous_header.name).is_file():
          copy_file(previous_header, new_include_path)
      # compile
      elf_path = self._get_elf_path(platform_name, app_name, target_imp_class, build_mode)
      self.devkit.add_new_job('app_build', True, 'start')
      shell_result = run_shell_cmd('make --no-print-directory _build', build_path, stderr=subprocess.STDOUT, prints_when_error=False, asserts_when_error=False)
      self.devkit.add_process_log(shell_result, is_user=True)
      self.devkit.check_log(True)
      compile_correctly = False
      if elf_path.is_file():
        elf_analysis_file = self.devkit.get_devkit_path('util','check_functions_in_elf.py')
        error_function_list_file = self.devkit.get_devkit_path('util','error_function_list.txt')
        output_file = elf_path.parent / 'check_result.txt'
        cmd = f'{self.config.python3_cmd} {elf_analysis_file} -elf {elf_path} -e {error_function_list_file} -o {output_file}'
        run_shell_cmd(cmd, elf_path.parent)
        assert output_file.is_file, output_file
        error_contents = output_file.read_text(encoding='utf8')
        if error_contents:
          # elf_path.unlink()
          self.devkit.handle_output(error_contents)
        compile_correctly = True
        
      if compile_correctly:
        verify_path = elf_path.parent / 'compile_correctly'
      else:
        verify_path = elf_path.parent / 'compile_wrong'
      verify_path.touch()

      if not compile_correctly:
        self.devkit.add_new_job('app_build_analysis', True, 'start')
        analyze_build_log_file = self._get_env_file('util', 'analyze_build_log.py')
        build_log_path = self.devkit.engine_log.log_path / 'rvx_app_build.log'
        analyze_log_file = self.devkit.engine_log.log_path / 'rvx_app_build_analysis.log'
        #cmd = f'{self.config.python3_cmd} {analyze_build_log_file} -i {build_log_path} -o {analyze_log_file}'
        cmd = f'{self.config.python3_cmd} {analyze_build_log_file} -i {build_log_path}'
        shell_result = run_shell_cmd(cmd, stderr=subprocess.STDOUT, prints_when_error=False, asserts_when_error=False)
        self.devkit.add_process_log(shell_result, is_user=True)
        self.devkit.check_log(True)
        assert 0, 'compile_wrong'

      # make previous
      if elf_path.is_file() and self.config.builds_incrementally:
        if not is_incremental:
          remove_directory(previous_success_file_path)
          previous_success_file_path.mkdir()
        move_files(new_source_path, previous_success_file_path)
        move_files(new_include_path, previous_success_file_path)
        move_files(new_etc_path, previous_success_file_path)
        remove_directory(new_source_path)
        remove_directory(new_include_path)
        remove_directory(new_etc_path)

  def app_build(self, platform_name:str, app_name:str, target_imp_class:str, build_mode:str):
    assert platform_name
    assert app_name
    assert target_imp_class
    assert build_mode

    self.__check_target_imp_class(target_imp_class)

    # prepare
    platform_path = self._get_platform_path(platform_name)
    app_path = self._get_app_path(platform_name,app_name)
    build_path = self._get_build_path(platform_name, app_name, target_imp_class, build_mode)
    self.app_build_dir(platform_name, app_name, target_imp_class, build_mode)

    # compile
    is_incremental = self.__prepare_app_source(platform_name,app_name, target_imp_class, build_mode)
    self.app_compile(platform_name,app_name, target_imp_class, build_mode, is_incremental)

  def app_clean(self, platform_name:str, app_name:str, target_imp_class:str):
    if app_name=='Base':
      for app_name in self.info_app_list(platform_name):
        self.__app_clean_local(platform_name, app_name, target_imp_class)
    else:
      self.__app_clean_local(platform_name, app_name, target_imp_class)
  
  def __app_clean_local(self, platform_name:str, app_name:str, target_imp_class:str):
    assert platform_name
    assert app_name

    app_path = self._get_app_path(platform_name,app_name)
    exclude_list = set(('Makefile','src','include','rvx_each.mh','each_app_config.mh','compile_list'))
    RvxWorkspace.__clean(app_path,exclude_list)

  def __generate_hex(self, platform_name:str, app_name:str, target_imp_class:str, build_mode:str, hex_prefix:str, output_path:Path):
    elf_file = self._get_elf_path(platform_name, app_name, target_imp_class, build_mode)
    assert elf_file.is_file(), elf_file
    memory_info = self._get_memory_info(platform_name)
    config = ' '.join(['-'+' '.join(x) for x in memory_info])
    generate_hex_file = self.devkit.get_devkit_path('util','generate_hex.py')
    cmd = f'{self.config.python3_cmd} {generate_hex_file} -elf {elf_file} {config} -o {output_path}'
    if target_imp_class=='rtl':
      cmd += ' --stores_bss'
    if hex_prefix:
      cmd += f' -p {hex_prefix}'
    run_shell_cmd(cmd,output_path)

  def app_new(self, platform_name:str, app_name:str):
    assert platform_name
    assert app_name
    app_path = self._get_app_path(platform_name, app_name)
    assert not app_path.is_dir()
    (app_path/'src').mkdir(parents=True)
    template_file = self.devkit.get_devkit_path('makefile','Makefile.app.template')
    target_makefile = app_path / 'Makefile'
    configure_template_file(template_file, target_makefile)
    self.app_compile_list(platform_name, app_name)
    #copy_file(self._get_app_path(platform_name, 'hello')/'src'/'main.c', app_path/'src'/'main.c')

  def app_delete(self, platform_name:str, app_name:str):
    assert platform_name
    assert app_name

    app_path = self._get_app_path(platform_name, app_name)
    assert app_path.is_dir()
    remove_directory(app_path)

  def app_path(self, platform_name:str, app_name:str):
    return self._get_app_path(platform_name, app_name)

  def info_platform_list(self):
    return get_dir_list(self.workspace_path)

  def info_app_list(self, platform_name:str) -> list:
    assert platform_name
    app_base_path = self._get_app_base_path(platform_name)
    return get_dir_list(app_base_path)

  def info_verifying_sim_app_list(self, platform_name:str) -> list:
    assert platform_name
    return [s for s in self.info_app_list(platform_name) if s.startswith("verify_") and not s.endswith("_fpga")]

  def info_verifying_fpga_app_list(self, platform_name:str) -> list:
    assert platform_name
    return [s for s in self.info_app_list(platform_name) if s.startswith("verify_") and not s.endswith("_sim")]

  def info_imp_class_list(self):
    return self.imp_class.imp_class_list
  
  def info_fpga_list(self):
    return self.imp_class.fpga_list

  def info_imp_instance_list(self, platform_name:str):
    instance_list = self.imp_class.unique_instance_list
    instance_list += self.info_fpga_instance_list(platform_name)
    return instance_list

  def info_fpga_instance_list(self, platform_name:str):
    fpga_set = frozenset(self.imp_class.fpga_list)
    instance_list = []
    platform_path = self._get_platform_path(platform_name)
    for element in platform_path.glob('imp_*'):
      if element.is_dir():
        name_list = element.name.split('_')
        if len(name_list)<2:
          continue
        if name_list[1] not in fpga_set:
          continue
        instance_list.append((element.name,name_list[1],'fpga'))
    return instance_list
  
  def print_app_list(self, platform_name:str):
    app_list = self.info_app_list(platform_name)
    contents = '\n'.join(app_list)
    self.devkit.handle_output(contents)

  def gen_app_list(self, platform_name:str, imp_instance_path:Path):
    app_list = self.info_app_list(platform_name)
    for app_name in app_list:
      (imp_instance_path / app_name).touch(exist_ok=True)

  def platform_freeze(self, platform_name:str):
    assert self._get_platform_xml(platform_name).is_file()
    self._get_platform_freeze_path(platform_name).mkdir(exist_ok=True)
    move_files(self._get_platform_xml(platform_name), self._get_platform_freeze_xml_path(platform_name))
    remove_file(self._get_arch_path(platform_name) / '.gitignore')
    print('[WARNING] Add \'%s\' to the git if needed' % self._get_platform_freeze_xml_path(platform_name).relative_to(self._get_platform_path(platform_name)))

  def platform_unfreeze(self, platform_name:str):
    assert self._get_platform_freeze_xml_path(platform_name).is_file()
    move_files(self._get_platform_freeze_xml_path(platform_name), self._get_platform_xml(platform_name))
    remove_directory(self._get_platform_freeze_path(platform_name))
    self.devkit.set_gitignore('all', self._get_arch_path(platform_name))
    print('[WARNING] Add \'%s\' to the git if needed' % self._get_platform_xml(platform_name).relative_to(self._get_platform_path(platform_name)))
    
  def platform_clean(self, platform_name:str):
    if platform_name=='Base':
      for platform_name in self.info_platform_list():
        self.__platform_clean(platform_name)
    else:
      self.__platform_clean(platform_name)
  
  def platform_clean_all_imp(self, platform_name:str):
    platform_path = self._get_platform_path(platform_name)
    assert platform_path.is_dir(), platform_path
    for x in platform_path.glob('imp_*'):
      if x.is_dir():
        remove_directory(x)
  
  def __platform_clean(self, platform_name:str):
    platform_path = self._get_platform_path(platform_name)
    assert platform_path.is_dir(), platform_path
    for x in platform_path.glob('*.tar.gz'):
      remove_file(x)
    for x in platform_path.glob('*.tar'):
      remove_file(x)
    for x in platform_path.glob('*.zip'):
      remove_file(x)
    if self._get_platform_xml(platform_name).is_file():
      remove_directory(platform_path/'arch')
      remove_directory(platform_path/'header')
    remove_directory(platform_path/'sim_rtl')
    
    util_path = self._get_platform_util_path(platform_name)
    if util_path.is_dir():
      run_shell_cmd('make --no-print-directory clean', util_path)

    self.platform_clean_all_imp(platform_name)
    self.app_clean(platform_name, 'Base', None)

  def platform_distclean(self, platform_name:str):
    assert platform_name
    platform_path = self._get_platform_path(platform_name)
    self.platform_clean(platform_name)
    #remove_directory(platform_path/'app')
    remove_directory(platform_path/'user')
    remove_directory(platform_path/'fpga_component')

  def platform_import(self, platform_name:str):
    assert platform_name
    etri_home_path = get_path_from_os_env('RVX_ETRI_HOME', asserts_when_missing=True)
    assert self.workspace_path.parent!=etri_home_path, self.workspace_path
    ws_list = (etri_home_path/'platform', etri_home_path/'platform_lec', etri_home_path/'platform_test', etri_home_path/'platform_hmcu')
    platform_path_to_import = None
    for ws in ws_list:
      candidate = ws / platform_name
      if candidate.exists():
        platform_path_to_import = candidate
        break
    if platform_path_to_import:
      platform_path = self._get_platform_path(platform_name)
      if platform_path.exists():
        remove(platform_path)
      copy_directory(platform_path_to_import, platform_path)
      self.platform_clean(platform_name)
      remove_directory(platform_path/'fpga_component')

  def platform_testbench(self, platform_name:str):
    assert platform_name
    platform_path = self._get_platform_path(platform_name)
    target_path = platform_path / 'app'
    copy_directory(self.config.devkit_path/'testbench', target_path)

  def platform_app_base(self, platform_name:str):
    target_makefile = self._get_platform_path(platform_name) / 'app' / 'Makefile'
    if not target_makefile.is_file():
      if target_makefile.parent.exists():
        remove(target_makefile.parent)
      target_makefile.parent.mkdir()
      template_file = self.devkit.get_devkit_path('makefile','Makefile.app_base.template')
      configure_template_file(template_file, target_makefile)
  
  def platform_system_app(self, platform_name:str):
    platform_path = self._get_platform_path(platform_name)
    source_path = self.devkit.get_devkit_path('system_app')
    target_path = platform_path / 'app'
    assert target_path.is_dir()
    copy_directory(source_path, target_path)

  def platform_user(self, platform_name:str):
    target_path = self._get_user_path(platform_name)
    if not target_path.is_dir():
      copy_directory(self.config.devkit_path/'user', target_path)
      for element in target_path.glob('**/README.txt'):
        if element.is_file():
          remove_file(element)
  
  def platform_util(self, platform_name:str):
    target_makefile = self._get_platform_util_path(platform_name) / 'Makefile'
    target_makefile.parent.mkdir(exist_ok=True)
    template_file = self.devkit.get_devkit_path('makefile','Makefile.util.template')
    configure_template_file(template_file, target_makefile)

  def platform_new(self, platform_name:str):
    assert platform_name
    platform_path = self._get_platform_path(platform_name)
    if platform_path.exists():
      remove(platform_path)
    platform_path.mkdir()
    template_file = self.devkit.get_devkit_path('makefile','Makefile.platform.template')
    target_makefile = platform_path / 'Makefile'
    configure_template_file(template_file, target_makefile)

    self.platform_app_base(platform_name)

  def platform_delete(self, platform_name:str):
    assert platform_name
    platform_path = self._get_platform_path(platform_name)
    if platform_path.is_dir():
      remove_directory(platform_path)

  def platform_file(self, platform_name:str):
    return self._get_platform_xml(platform_name)

  def __handle_generated_user_template_file(self, platform_name:str, generated_user_file:Path, uses_directly:bool):
    arch_path = self._get_arch_path(platform_name)
    relative_path = generated_user_file.relative_to(arch_path)
    template_user_file = self._get_user_template_path(platform_name) / generated_user_file.name
    target_user_file = self._get_user_path(platform_name) / relative_path
    if generated_user_file.is_file():
      self.platform_user(platform_name)
      template_user_file.parent.mkdir(parents=True, exist_ok=True)
      if template_user_file.is_file():
        remove_file(template_user_file)
      generated_user_file.rename(template_user_file)
      if uses_directly:
        if not target_user_file.is_file():
          target_user_file.parent.mkdir(parents=True, exist_ok=True)
          copy_file(template_user_file,target_user_file)
    else:
      if target_user_file.is_file():
        print(f'[WARNING] The platform does NOT have user region, so \"{target_user_file.name}\" will be ignored')

  def __platform_syn_after(self, platform_name:str):
    # user_region
    user_region_file = self._get_arch_path(platform_name) / 'rtl' / 'include' / f'{platform_name}_user_region.vh'
    self.__handle_generated_user_template_file(platform_name, user_region_file, True)
    
    # user template
    user_module_dec_file = self._get_arch_path(platform_name) / 'xml' / 'user_module_dec.xml'
    if user_module_dec_file.is_file():
      xml_tree = parse(str(user_module_dec_file))
      xml_root = xml_tree.getroot()
      assert xml_root.tag=='rvx', xml_root.tag
      for dec_ip in xml_root.findall('dec_ip'):
        dec_ip_name = dec_ip.find('name').text
        hdl_file = self._get_arch_path(platform_name) / 'rtl' / 'src' / f'{dec_ip_name}.v'
        assert hdl_file.is_file()
        self.__handle_generated_user_template_file(platform_name, hdl_file, False)
    
    self.app_clean(platform_name, 'Base', None)
    
  def platform_syn(self, platform_name:str):
    assert platform_name
    self.platform_syn_arch(platform_name)
    self.check_platform_synthesized_correctly(platform_name, True)
    self.__platform_syn_after(platform_name)

  def platform_syn_arch(self, platform_name:str):
    assert platform_name
    platform_path = self._get_platform_path(platform_name)
    self.devkit.add_new_job('platform_syn_arch', True, 'start')
    shell_result = run_shell_cmd('make --no-print-directory _syn_arch', platform_path, prints_when_error=False, asserts_when_error=False)
    if self._get_arch_path(platform_name).is_dir():
      self.devkit.set_gitignore('all', self._get_arch_path(platform_name))
    self.devkit.add_process_log(shell_result, is_user=True)
    self.devkit.check_log(True)

  def check_platform_synthesized_correctly(self, platform_name:str, logs_success:bool=False):
    rtl_file = self._get_arch_path(platform_name) / 'rtl' / 'src' / f'{platform_name}.v'
    if rtl_file.is_file():
      if logs_success:
        self.devkit.add_new_job('platform_syn_check', True, 'start')
        self.devkit.add_log('', 'done', is_user=True)
    elif len(tuple(rtl_file.parent.glob('*.v'))) > 0:
      self.devkit.add_new_job('platform_syn_check', True, 'start')
      self.devkit.add_log('Wrong platform name in XML', 'error', False, is_user=True)
    else:
      self.devkit.add_new_job('platform_syn_check', True, 'start')
      self.devkit.add_log('Synthesis is required. Previous try can have an error', 'error', False, is_user=True)
    self.devkit.check_log()

  def platform_imp_chip(self, platform_name:str, target_imp_class:str, imp_instance_path:Path):
    self.check_platform_synthesized_correctly(platform_name)
    imp_instance_path = self._mkdir_imp_instance_path(platform_name, 'chip', target_imp_class, imp_instance_path)
    self.devkit.set_gitignore('all', imp_instance_path)
    self.sim_rtl_path(platform_name, imp_instance_path)

  def platform_imp_fpga_dir(self, platform_name:str, target_imp_class:str, imp_instance_path:Path):
    return self._mkdir_imp_instance_path(platform_name, 'fpga', target_imp_class, imp_instance_path)

  def platform_sim_rtl(self, platform_name:str):
    self.platform_sim_rtl_syn(platform_name)
    self.sim_rtl_path(platform_name, self._get_sim_rtl_path(platform_name))
    self.gen_app_list(platform_name, self._get_sim_rtl_path(platform_name))
  
  @staticmethod
  def _write_path_var_file(var_dict:dict, lang:str, output_file:Path):
    line_list = []
    for name, value in var_dict.items():
      if value is None:
        if lang=='makefile':
          line_list.append(f'{name}=')
        continue
      value = Path(os.path.normpath(value)).as_posix()
      if lang=='tcl':
        line_list.append(f'set {name} {value}')
      elif lang=='makefile':
        line_list.append(f'{name}={value}')
      else:
        assert 0, lang
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text('\n'.join(line_list), encoding='utf8')

  def _get_hw_path_var_dict(self, platform_name:str):
    var_dict = {}
    var_dict['RVX_HWLIB_BASIC_HOME'] = self.config.hwlib_basic_path
    var_dict['RVX_HWLIB_SPECIAL_HOME'] = self.config.hwlib_special_path
    var_dict['MUNOC_HW_HOME'] = self.config.munoc_path
    for ip_name in ('starc', 'dca'):
      candidate_list = [self._get_user_path(platform_name) / ip_name,
                        getattr(self.config, f'{ip_name}_path')]
      var_dict[f'{ip_name.upper()}_HW_HOME'] = select_path(candidate_list, False)
    return var_dict

  def sim_rtl_path(self, platform_name:str, imp_instance_path:Path):
    var_dict = {x: y for x, y in self._get_hw_path_var_dict(platform_name).items() if not x.startswith('RVX_')}
    RvxWorkspace._write_path_var_file(var_dict, 'makefile', imp_instance_path/'set_path.mh')

  def platform_sim_rtl_syn(self, platform_name:str):
    self.check_platform_synthesized_correctly(platform_name)
    run_shell_cmd('make --no-print-directory _sim_rtl_syn', self._get_platform_path(platform_name))
    self.sim_rtl_pll(platform_name)
    self.devkit.set_gitignore('all', self._get_sim_rtl_path(platform_name))

  def sim_rtl_pll(self, platform_name:str):
    tic_xml = self.imp_class.file_dict['rtl']
    elab_file = self.devkit.get_devkit_path('elab','generate_pll_module.py')
    imp_dependent_xml = self._get_arch_path(platform_name) / 'xml' / 'imp_dependent.xml'
    assert imp_dependent_xml.is_file(), imp_dependent_xml
    output_dir = self._get_sim_rtl_path(platform_name)
    run_shell_cmd(f'{self.config.python3_cmd} {elab_file} -m {imp_dependent_xml} -tic_name rtl -tic_xml {tic_xml} -o {output_dir}')
  
  def sim_rtl_script(self, platform_name:str, sim_path:Path):
    if self.config.rtl_simulator=='modelsim' or self.config.rtl_simulator=='questasim':
      run_script = sim_path / 'run.do'
      if not run_script.is_file():
        contents = ''
        contents += 'set NumericStdNoWarnings 1'
        contents += '\n'
        contents += 'run -all'
        run_script.write_text(contents, encoding='utf8')
      debug_script = sim_path / 'debug.do'
      if not debug_script.is_file():
        contents = ''
        contents += 'set NumericStdNoWarnings 1'
        contents += '\n'
        contents += 'add log -r /*'
        contents += '\n'
        contents += 'run -all'
        debug_script.write_text(contents, encoding='utf8')
    elif self.config.rtl_simulator=='ncsim' or self.config.rtl_simulator=='xcelium':
      run_script = sim_path / 'run.tcl'
      if not run_script.is_file():
        copy_file(self.config.devkit_path/'makefile'/'sim.tcl', run_script)
      debug_script = sim_path / 'debug.tcl'
      if not debug_script.is_file():
        copy_file(self.config.devkit_path/'makefile'/'sim.tcl', debug_script)
    elif self.config.rtl_simulator=='xsim':
      run_script = sim_path / 'run.tcl'
      if not run_script.is_file():
        run_script.write_text('run all\nquit\n', encoding='utf8')
      debug_script = sim_path / 'debug.tcl'
      if not debug_script.is_file():
        debug_script.write_text('log_wave -recursive *\nrun all\nquit\n', encoding='utf8')
    else:
      assert 0, 'Please check .rvx_tool_config'
  
  def sim_rtl_build(self, platform_name:str, app_name:str, build_mode:str):
    self.app_build(platform_name, app_name, 'rtl', build_mode)

  def sim_rtl_clean_build(self, platform_name:str, app_name:str, build_mode:str, sim_path:Path):
    self.app_clean(platform_name, app_name, 'rtl')
    for x in ('sram.hex','crm.hex','dram.hex'):
      remove_file(sim_path/x)

  def sim_rtl_after_build(self, platform_name:str, app_name:str, build_mode, sim_path:Path):
    self.__generate_hex(platform_name,app_name,'rtl',build_mode,None,sim_path)
    calculate_hex_size_file = self.devkit.get_devkit_path('util','calculate_hex_size.py')
    hex_size_flie = sim_path / 'include' / 'hex_size.vh'
    hex_list = ' '.join([ str(sim_path/x) for x in ('sram.hex','crm.hex','dram.hex')])
    cmd = f'{self.config.python3_cmd} {calculate_hex_size_file} -i {hex_list} -o {hex_size_flie}'
    run_shell_cmd(cmd,sim_path)

  def sim_rtl_compile_test(self, platform_name:str, sim_path:Path):
    run_shell_cmd(f'make --no-print-directory _compile_test RTL_SIMULATOR={self.config.rtl_simulator}',sim_path, stdout=None, stderr=None, asserts_when_error=False)

  def sim_rtl_compile_test_all(self, platform_name:str, sim_path:Path):
    run_shell_cmd(f'make --no-print-directory _compile_test_all RTL_SIMULATOR={self.config.rtl_simulator}',sim_path, stdout=None, stderr=None, asserts_when_error=False)

  def sim_rtl_compile_rtl_normal(self, platform_name:str, sim_path:Path):
    run_shell_cmd(f'make --no-print-directory _compile_rtl_normal RTL_SIMULATOR={self.config.rtl_simulator}',sim_path, stdout=None, stderr=None, asserts_when_error=False)
  
  def sim_rtl_compile_rtl_debug(self, platform_name:str, sim_path:Path):
    run_shell_cmd(f'make --no-print-directory _compile_rtl_debug RTL_SIMULATOR={self.config.rtl_simulator}',sim_path, stdout=None, stderr=None, asserts_when_error=False)

  def sim_rtl_compile_rtl_debug_init(self, platform_name:str, sim_path:Path):
    run_shell_cmd(f'make --no-print-directory _compile_rtl_debug_init RTL_SIMULATOR={self.config.rtl_simulator}',sim_path, stdout=None, stderr=None, asserts_when_error=False)

  def _sim_rtl_dump_dir(self, sim_path:Path):
    dump_dir = sim_path / 'dump'
    if dump_dir.is_dir():
      remove_directory(dump_dir)
    dump_dir.mkdir()

  def sim_rtl_run_rtl(self, platform_name:str, sim_path:Path):
    self._sim_rtl_dump_dir(sim_path)
    cmd = f'make --no-print-directory _run_rtl RTL_SIMULATOR={self.config.rtl_simulator}'
    if self.devkit.is_called_by_gui:
      run_shell_cmd_with_terminal(cmd, sim_path)
    else:
      run_shell_cmd(cmd, sim_path, stdout=None, stderr=None, asserts_when_error=False)
    self.uncompress_dump(sim_path)

  def sim_rtl_debug_rtl(self, platform_name:str, sim_path:Path):
    self._sim_rtl_dump_dir(sim_path)
    cmd = f'make --no-print-directory _debug_rtl RTL_SIMULATOR={self.config.rtl_simulator}'
    if self.devkit.is_called_by_gui:
      run_shell_cmd_with_terminal(cmd, sim_path)
    else:
      run_shell_cmd(cmd, sim_path, stdout=None, stderr=None, asserts_when_error=False)
    self.uncompress_dump(sim_path)

  def sim_rtl_debug_view_rtl(self, platform_name:str, sim_path:Path):
    self._sim_rtl_dump_dir(sim_path)
    cmd = f'make --no-print-directory _debug_view_rtl RTL_SIMULATOR={self.config.rtl_simulator}'
    if self.devkit.is_called_by_gui:
      run_shell_cmd_with_terminal(cmd, sim_path)
    else:
      run_shell_cmd(cmd, sim_path, stdout=None, stderr=None, asserts_when_error=False)
    self.uncompress_dump(sim_path)

  def sim_rtl_run(self, platform_name:str, app_name:str, build_mode, sim_path:Path):
    self.sim_rtl_build(platform_name,app_name,build_mode)
    self.sim_rtl_after_build(platform_name,app_name,build_mode,sim_path)
    self.sim_rtl_compile_rtl_normal(platform_name,sim_path)
    self.sim_rtl_script(platform_name, sim_path)
    self.sim_rtl_run_rtl(platform_name,sim_path)

  def sim_rtl_debug(self, platform_name:str, app_name:str, build_mode, sim_path:Path):
    self.sim_rtl_build(platform_name,app_name,build_mode)
    self.sim_rtl_after_build(platform_name,app_name,build_mode,sim_path)
    self.sim_rtl_compile_rtl_debug(platform_name,sim_path)
    self.sim_rtl_script(platform_name, sim_path)
    self.sim_rtl_debug_rtl(platform_name,sim_path)

  def sim_rtl_debug_init(self, platform_name:str, app_name:str, build_mode, sim_path:Path):
    self.sim_rtl_build(platform_name,app_name,build_mode)
    self.sim_rtl_after_build(platform_name,app_name,build_mode,sim_path)
    self.sim_rtl_compile_rtl_debug_init(platform_name,sim_path)
    self.sim_rtl_script(platform_name, sim_path)
    self.sim_rtl_debug_rtl(platform_name,sim_path)

  def sim_rtl_debug_view(self, platform_name:str, app_name:str, build_mode, sim_path:Path):
    self.sim_rtl_build(platform_name,app_name,build_mode)
    self.sim_rtl_after_build(platform_name,app_name,build_mode,sim_path)
    self.sim_rtl_compile_rtl_debug(platform_name,sim_path)
    self.sim_rtl_script(platform_name, sim_path)
    self.sim_rtl_debug_view_rtl(platform_name,sim_path)

  def sim_rtl_view(self, platform_name:str, sim_path:Path):
    run_shell_cmd(f'make --no-print-directory _view RTL_SIMULATOR={self.config.rtl_simulator}', sim_path, stdout=None, stderr=None, asserts_when_error=False)

  def sim_rtl_compile_check(self, platform_name:str, sim_path:Path):
    run_shell_cmd(f'make --no-print-directory _check RTL_SIMULATOR={self.config.rtl_simulator}', sim_path, stdout=None, stderr=None, asserts_when_error=False)
  
  def _sim_rtl_run_verify(self, platform_name:str, app_name:str, build_mode, sim_path:Path, run_log_path:Path) -> bool:
    run_log_path.unlink(missing_ok=True)
    self.sim_rtl_run(platform_name, app_name, build_mode, sim_path)
    self.backup_app_log(run_log_path, app_name)

    result = self.get_app_return_from_log(run_log_path)
    if result:
      contents = f'\'{app_name}\' is verified'
    else:
      contents = f'\'{app_name}\' is NOT verified'
    self.devkit.handle_output(contents)
    return result
  
  def sim_rtl_run_verify(self, platform_name:str, app_name:str, build_mode, sim_path:Path) -> None:
    run_log_path = sim_path / get_hdlsim_filename(self.config.rtl_simulator, 'run.log')
    self._sim_rtl_run_verify(platform_name, app_name, build_mode, sim_path, run_log_path)
  
  def sim_rtl_verify_apps(self, platform_name:str, build_mode:str, sim_path:Path):
    app_list = self.info_verifying_sim_app_list(platform_name)
    contents = '\n'.join(app_list)
    self.devkit.handle_output(contents)

    for app_name in app_list:
      self.app_clean(platform_name, app_name, 'rtl')
      self.sim_rtl_build(platform_name, app_name, build_mode)
    
    run_log_path = sim_path / get_hdlsim_filename(self.config.rtl_simulator, 'run.log')
    app_run_log_path = self.get_app_log_path(run_log_path, '*')
    remove_files(app_run_log_path.parent, app_run_log_path.name)
    
    result = True
    for app_name in app_list:
      result = self._sim_rtl_run_verify(platform_name, app_name, build_mode, sim_path, run_log_path)
      if not result:
        break
    
    if result:
      print ('All apps are verified')
  
  def _mkdir_imp_instance_path(self, platform_name:str, imp_type:str, target_imp_class:str, imp_instance_path:Path):
    self.check_platform_synthesized_correctly(platform_name)
    platform_path = self._get_platform_path(platform_name)
    if not imp_instance_path:
      date = datetime.datetime.now().strftime('%Y-%m-%d')
      imp_instance_name = f'imp_{target_imp_class}_{date}'
      imp_instance_path = platform_path / imp_instance_name

    # backup
    if imp_instance_path.is_dir():
      success = False
      for index in range(100):
        backup_path = Path(str(imp_instance_path) + f'-{index:02d}')
        if not backup_path.is_dir():
          imp_instance_path.rename(backup_path)
          success = True
          break
      assert success
      print(f'Previous workspace is backuped as {backup_path}')
    
    #
    imp_instance_path.mkdir()
    #
    template_file = self.devkit.get_devkit_path('makefile',f'Makefile.imp_{imp_type}.template')
    target_file = imp_instance_path / 'Makefile'
    config_list = (('PLATFORM_NAME', platform_name),
                 ('TARGET_IMP_CLASS', target_imp_class))
    configure_template_file(template_file, target_file, config_list)
    #
    platform_xml = self._get_platform_xml(platform_name)
    copy_file(platform_xml, imp_instance_path / platform_xml.name)
    return imp_instance_path

  @staticmethod
  def generate_design_info(devkit_git_version:str, home_git_version:str, username:str, home_git_name:str):
    bw_username = 'BW_USERNAME'
    bw_git_name = 'BW_GIT_NAME'
    bw_git_version = 'BW_GIT_VERSION'
    bw_date = 'BW_DATE'
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    line_list = []
    line_list.append(f'wire [{bw_username}-1:0] username_string = `FORMAT_STRING(\"{username}\");')
    line_list.append(f'wire [{bw_git_name}-1:0] home_git_name_string = `FORMAT_STRING(\"{home_git_name}\");')
    line_list.append(f'wire [{bw_git_version}-1:0] home_git_version_string = `FORMAT_STRING(\"{home_git_version}\");')
    line_list.append(f'wire [{bw_git_version}-1:0] devkit_git_version_string = `FORMAT_STRING(\"{devkit_git_version}\");')
    line_list.append(f'wire [{bw_date}-1:0] design_date_string = `FORMAT_STRING(\"{now}\");')
    return '\n'.join(line_list)

  def imp_fpga_info(self, imp_instance_path:Path):
    devkit_git_version = self.devkit.devkit_git_info()
    home_git_version = self.devkit.home_git_info()
    username = self.devkit.username()
    home_git_name = self.devkit.home_git_name()
    design_info_text = RvxWorkspace.generate_design_info(devkit_git_version,home_git_version,username,home_git_name)
    design_info_path = imp_instance_path / 'include' / 'ervp_design_info.vh'
    design_info_path.parent.mkdir(parents=True, exist_ok=True)
    design_info_path.write_text(design_info_text, encoding='utf8')

  def imp_fpga_module(self, platform_name:str, target_imp_class:str, imp_instance_path:Path):
    assert imp_instance_path.is_dir(), imp_instance_path
    self.check_platform_synthesized_correctly(platform_name)

    imp_instance_name = imp_instance_path.name
    platform_path = self._get_platform_path(platform_name)
    run_shell_cmd(f'make --no-print-directory _imp_fpga_module TARGET_IMP_CLASS={target_imp_class} IMP_INSTANCE_DIR={imp_instance_path.as_posix()}', platform_path)

  def imp_fpga_top_module(self, platform_name:str, target_imp_class:str, imp_instance_path:Path):
    tic_xml = self.imp_class.file_dict[target_imp_class]
    elab_file = self.devkit.get_devkit_path('elab','generate_fpga_top_module.py')
    top_module_xml = self._get_arch_path(platform_name) / 'xml' / 'top_module_dec.xml'
    output_dir = imp_instance_path / 'src'
    run_shell_cmd(f'{self.config.python3_cmd} {elab_file} -top {top_module_xml} -tic_name {target_imp_class} -tic_xml {tic_xml} -o {output_dir}')

  def imp_fpga_pll(self, platform_name:str, target_imp_class:str, imp_instance_path:Path):
    tic_xml = self.imp_class.file_dict[target_imp_class]
    elab_file = self.devkit.get_devkit_path('elab','generate_pll_module.py')
    imp_dependent_xml = self._get_arch_path(platform_name) / 'xml' / 'imp_dependent.xml'
    output_dir = imp_instance_path
    run_shell_cmd(f'{self.config.python3_cmd} {elab_file} -m {imp_dependent_xml} -tic_name {target_imp_class} -tic_xml {tic_xml} -o {output_dir}')
  
  @staticmethod
  def imp_fpga_set_path_path(imp_instance_path:Path):
    return imp_instance_path/'set_path.tcl'

  def imp_fpga_path(self, platform_name:str, target_imp_class:str, imp_instance_path:Path):
    var_dict = {}
    var_dict['RVX_DEVKIT_HOME'] = self.config.devkit_path
    var_dict['PLATFORM_DIR'] = imp_instance_path.parent
    var_dict['FPGA_NAME'] = target_imp_class
    var_dict['FPGA_DEPENDENT_DIR'] = self._get_imp_class_path(target_imp_class)
    var_dict.update(self._get_hw_path_var_dict(platform_name))
    RvxWorkspace._write_path_var_file(var_dict, 'tcl', self.imp_fpga_set_path_path(imp_instance_path))
  
  def imp_fpga_tcl(self, platform_name:str, target_imp_class:str, imp_instance_path:Path):
    ## tcl is dependent on local info
    # check
    assert imp_instance_path.is_dir(), imp_instance_path
    self.check_platform_synthesized_correctly(platform_name)
    imp_dict = self.imp_class.get_imp_class_info(target_imp_class)
    fpga_info_dict = self.imp_class.get_fpga_info(target_imp_class)

    # set_path
    self.imp_fpga_path(platform_name, target_imp_class, imp_instance_path)
    
    # set_fpga
    image_size = int(fpga_info_dict['image_size'])
    image_size_Mbytes = (image_size >> 20) + 1
    if 'separate_flash' in fpga_info_dict:
      flash_base_addr = 0
    else:
      flash_base_addr = ((image_size >> 16)+1) << 16      
    template_file = self._get_env_file('xilinx', 'set_fpga.tcl.template')
    output_file = imp_instance_path / 'set_fpga.tcl'
    config_list = (('FPGA_PART', fpga_info_dict['part']),
                   ('FLASH_BASE_ADDR', f'32\'h{flash_base_addr:x}'),
                   ('FLASH_INTERFACE_TYPE', fpga_info_dict['flash_interface_type'])
                  )
    configure_template_file(template_file, output_file, config_list)

    # gen_mcs
    image_size_Mbytes2 = 1
    while image_size_Mbytes2 < image_size_Mbytes:
      image_size_Mbytes2 <<= 1
    template_file = self._get_env_file('xilinx', 'gen_mcs.tcl.template')
    output_file = imp_instance_path / 'gen_mcs.tcl'
    config_list = (('FLASH_INTERFACE_TYPE', fpga_info_dict['flash_interface_type']),
                 ('PROM_SIZE', str(image_size_Mbytes2)))
    configure_template_file(template_file, output_file, config_list)

    # set_config_memory
    template_file = self._get_env_file('xilinx', 'set_config_memory.tcl.template')
    output_file = imp_instance_path / 'set_config_memory.tcl'
    config_list = (('CFG_MEM', fpga_info_dict['cfg_mem']),)
    configure_template_file(template_file, output_file, config_list)

    # set_design
    template_file = self.devkit.get_devkit_path('xilinx','set_design.tcl.template')
    target_file = imp_instance_path / 'set_design.tcl'
    config_list = (('TOP_MODULE', f'{platform_name.upper()}_FPGA'),
                   ('FPGA_NAME', target_imp_class)
                  )
    configure_template_file(template_file, target_file, config_list)

    # set_fpga_syn_env
    hw_define_dict = self._get_hw_define_dict(platform_name)
    xci_list = []
    xci_name_set = set()
    general_xci_path = ('${PLATFORM_DIR}', 'fpga_component', target_imp_class, 'xci')
    if 'INCLUDE_DDR' in hw_define_dict:
      dram_type = fpga_info_dict['dram']
      if 'INCLUDE_SLOW_DRAM' in hw_define_dict:
        xci_name = f'xilinx_{dram_type}_ctrl_axi32'
      elif 'INCLUDE_FAST_DRAM' in hw_define_dict:
        xci_name = f'xilinx_{dram_type}_ctrl_axi128'
      else:
        assert 0
      xci_name_set.add(xci_name)
    if 'INCLUDE_USER_DDR4' in hw_define_dict:
      xci_name = imp_dict['user_ddr4']
      xci_name_set.add(xci_name)
    if 'INCLUDE_USER_DDR3' in hw_define_dict:
      xci_name = imp_dict['user_ddr3']
      xci_name_set.add(xci_name)
    for xci_name in xci_name_set:
      xci_list.append('/'.join(general_xci_path + (xci_name, f'{xci_name}.xci')))

    template_file = self.devkit.get_devkit_path('xilinx','set_fpga_syn_env.tcl.template')
    target_file = imp_instance_path / 'set_fpga_syn_env.tcl'
    config_list = (('PLATFORM_DEPENDENT_XCI_LIST', '\n'.join([ f'lappend xci_list {xci}' for xci in xci_list])),)
    configure_template_file(template_file, target_file, config_list)

    # set_fpga_imp_env
    template_file = self.devkit.get_devkit_path('xilinx','set_fpga_imp_env.tcl.template')
    target_file = imp_instance_path / 'set_fpga_imp_env.tcl'
    configure_template_file(template_file, target_file, config_list)

    # set_tool_option
    target_file = imp_instance_path / 'set_tool_option.tcl'
    platform_path = self._get_platform_path(platform_name)
    candidate1_file = platform_path / 'user' / 'fpga' / target_imp_class / 'tcl' / target_file.name
    candidate2_file = platform_path / 'user' / 'fpga' / 'common' / 'tcl' / target_file.name
    if candidate1_file.is_file():
      copy_file(candidate1_file, target_file)
    elif candidate2_file.is_file():
      copy_file(candidate2_file, target_file)
    else:
      template_file = self.devkit.get_devkit_path('xilinx','set_tool_option.tcl.template')
      config_list = (('SYN_DESIGN_OPTION','{' + fpga_info_dict.setdefault('syn_strategy','') + '}'),
                     ('OPT_DESIGN_OPTION','{' + fpga_info_dict.setdefault('opt_strategy','') + '}'),
                     ('PLACE_DESIGN_OPTION','{' + fpga_info_dict.setdefault('place_strategy','') + '}'),
                     ('ROUTE_DESIGN_OPTION','{' + fpga_info_dict.setdefault('route_strategy','') + '}')
                    )
      configure_template_file(template_file, target_file, config_list)    
    
    # generated_clock and false_path
    logic_synthesis_info_xml_file = self._get_arch_path(platform_name) / 'xml' / 'logic_synthesis_info.xml'
    generated_clock_list = []
    false_path_list = []
    if logic_synthesis_info_xml_file.is_file():
      xml_tree = parse(logic_synthesis_info_xml_file)
      xml_root = xml_tree.getroot()
      assert xml_root.tag=='rvx', xml_root.tag
      for generated_clock in xml_root.findall('generated_clock'):
        clock_name = generated_clock.find('name').text
        clock_source = generated_clock.find('source').text
        clock_target = generated_clock.find('target').text
        line = f'create_generated_clock -name {clock_name} -source [get_pins {{i_platform/{clock_source}}}] -divide_by 1 [get_pins {{i_platform/{clock_target}}}]'
        generated_clock_list.append(line)
      for false_path in xml_root.findall('false_path'):
        source = false_path.find('source').text
        target = false_path.find('target').text
        assert target=='*', target
        line = f'set_false_path -through [get_pins {{{source}}}]'
        false_path_list.append(line)
    generated_clock_tcl_file = imp_instance_path / 'create_generated_clock.tcl'
    generated_clock_tcl_file.write_text('\n'.join(generated_clock_list), encoding='utf8')
    set_false_path_tcl_file = imp_instance_path / 'set_false_path.tcl'
    set_false_path_tcl_file.write_text('\n'.join(false_path_list), encoding='utf8')

    # set_ocd_env
    template_file = self._get_env_file('ocd', 'set_ocd_env.tcl.template')
    output_file = imp_instance_path / 'set_ocd_env.tcl'
    config_list = (('RVX_WORKSPACE', str(PurePosixPath(self.workspace_path))),
                 ('PLATFORM_NAME', platform_name))
    configure_template_file(template_file, output_file, config_list)

    # ocd cfg
    imp_dict = self.imp_class.get_imp_class_info(target_imp_class)
    usb2jtag = imp_dict['usb2jtag']
    vendor, product = usb2jtag.split(':')
    device_name = None
    ftdi_layout_init_value = None
    if (vendor, product)==('0403','6010'):
      device_name = 'Digilent Adept USB Device'
      ftdi_layout_init_value = '0x0808 0x0a1b'
    elif (vendor, product)==('15ba','002a'):
      device_name = 'Olimex OpenOCD JTAG ARM-USB-TINY-H'
      ftdi_layout_init_value = '0x0808 0x0a1b'
    elif (vendor, product)==('0403','6011'):
      device_name = 'Quad RS232-HS'
      ftdi_layout_init_value = '0x0818 0x0a1b'
    elif (vendor, product)==('0403','6014'):
      device_name = 'Digilent USB Device'
      ftdi_layout_init_value = '0x00e8 0x60eb'
    else:
      assert 0
    jtag_khz = imp_dict.get('jtag_khz', '10000')
    template_file = self._get_env_file('ocd', 'cfg.template')
    output_file = imp_instance_path / f'{target_imp_class}.cfg'
    config_list = (('VENDOR', vendor),
                 ('PRODUCT', product),
                ('DEVICE_NAME', device_name),
                   ('FTDI_LAYOUT_INIT_VALUE', ftdi_layout_init_value),
                   ('JTAG_KHZ', jtag_khz))
    configure_template_file(template_file, output_file, config_list)

  def imp_fpga_xci(self, platform_name:str, target_imp_class:str, imp_instance_path:Path):
    self.__check_fpga_name(target_imp_class)
    assert imp_instance_path.is_dir(), imp_instance_path
    target_fpga_componet_path = self._get_platform_path(platform_name) / 'fpga_component' / target_imp_class
    if not target_fpga_componet_path.is_dir():
      target_xci_path = target_fpga_componet_path / 'xci'
      if target_xci_path.is_dir():
        remove_directory(target_xci_path)
      target_xci_path.mkdir(parents=True)
      self.devkit.set_gitignore('all', self._get_platform_path(platform_name) / 'fpga_component')
      xci_library_path = self._get_imp_class_path(target_imp_class) / 'xci'
      if xci_library_path.is_dir():
        copy_directory(xci_library_path, target_xci_path)
      #
      template_file = self._get_env_file('makefile', 'Makefile.xci.template')
      output_file = self._get_platform_path(platform_name) / 'fpga_component' / target_imp_class / 'Makefile'
      config_list = (('FPGA_NAME', target_imp_class),
                   ('PROJECT_NAME', 'managed_ip_project'))
      configure_template_file(template_file, output_file, config_list)
      #
      fpga_info_dict = self.imp_class.get_fpga_info(target_imp_class)
      template_file = self._get_env_file('xilinx', 'make_ip_project.tcl.template')
      output_file = self._get_platform_path(platform_name) / 'fpga_component' / target_imp_class / 'make_ip_project.tcl'
      config_list = (('PROJECT_NAME', 'managed_ip_project'),
                   ('FPGA_PART', fpga_info_dict['part']))
      configure_template_file(template_file, output_file, config_list)

  def imp_fpga_clean(self, platform_name:str, target_imp_class:str, imp_instance_path:Path):
    exclude_list = set(('Makefile','each_imp.mh','src','include','xci', 'ila', 'set_fpga.tcl', 'set_design.tcl', 'set_fpga_imp_env.tcl', 'set_fpga_syn_env.tcl',
                        self.imp_fpga_set_path_path(imp_instance_path).name, 'set_ocd_env.tcl', 'gen_mcs.tcl', 'set_config_memory.tcl', f'{target_imp_class}.cfg',
                        'create_generated_clock.tcl', 'set_false_path.tcl','set_tool_option.tcl', 'syn_manually.tcl', 'pnr_manually.tcl', 'set_sdram_config.tcl',f'{platform_name}.xml'))
    RvxWorkspace.__clean(imp_instance_path,exclude_list)

  def platform_imp_fpga(self, platform_name:str, target_imp_class:str, imp_instance_path:Path):
    self.check_platform_synthesized_correctly(platform_name)    
    self.devkit.add_new_job('fpga_name_check', True, 'start')
    fpga_info_dict = self.imp_class.get_fpga_info(target_imp_class)
    if fpga_info_dict:
      self.devkit.add_log('', 'done', is_user=True)
    else:
      self.devkit.add_log(f'Wrong FPGA name: {target_imp_class}', 'error', is_user=True)
    self.devkit.check_log()
    imp_instance_path = self.platform_imp_fpga_dir(platform_name, target_imp_class, imp_instance_path)
    self.devkit.set_gitignore('all', imp_instance_path)
    self.imp_fpga_module(platform_name, target_imp_class, imp_instance_path)
    self.imp_fpga_top_module(platform_name, target_imp_class, imp_instance_path)
    self.imp_fpga_pll(platform_name, target_imp_class, imp_instance_path)
    self.imp_fpga_tcl(platform_name, target_imp_class, imp_instance_path)
    self.gen_app_list(platform_name, imp_instance_path)

  def imp_fpga_build(self, platform_name:str, app_name:str, target_imp_class:str, build_mode:str):
    self.__check_fpga_name(target_imp_class)
    self.app_build(platform_name,app_name, target_imp_class, build_mode)

  def imp_fpga_clean_build(self, platform_name:str, app_name:str, target_imp_class:str, build_mode:str, imp_instance_path:Path):
    self.app_clean(platform_name, app_name, target_imp_class)
    for app_hex in imp_instance_path.glob(f'{app_name}.*.hex'):
      remove_file(app_hex)

  def imp_fpga_after_build(self, platform_name:str, app_name:str, target_imp_class:str, build_mode:str, imp_instance_path:Path):
    assert imp_instance_path.is_dir(), imp_instance_path
    self.__generate_hex(platform_name,app_name,target_imp_class,build_mode,f'{app_name}.',imp_instance_path)
    # run_app
    template_file = self._get_env_file('ocd', 'run_app.tcl.template')
    output_file = imp_instance_path / f'run_{app_name}.tcl'
    config_list = (('APP_NAME', app_name),)
    configure_template_file(template_file, output_file, config_list)
    # program_app
    template_file = self._get_env_file('ocd', 'program_app.tcl.template')
    output_file = imp_instance_path / f'program_{app_name}.tcl'
    config_list = (('APP_NAME', app_name),)
    configure_template_file(template_file, output_file, config_list)

  def imp_fpga_run(self, platform_name:str, app_name:str, target_imp_class:str, build_mode:str, imp_instance_path:Path):
    assert imp_instance_path.is_dir(), imp_instance_path
    #
    self.imp_fpga_build(platform_name, app_name, target_imp_class, build_mode)
    self.imp_fpga_after_build(platform_name, app_name, target_imp_class, build_mode, imp_instance_path)
    #
    if not self.is_printf_running():
      self.imp_fpga_printf(target_imp_class, imp_instance_path, asserts_when_error=False)
    #
    script = imp_instance_path / f'run_{app_name}.tcl'
    assert script.is_file(), script
    self.__prepare_ocd(imp_instance_path)
    cmd = self._get_fpga_run_cmd(target_imp_class, imp_instance_path)
    cmd += f' -c \"source {PurePosixPath(script)}; exit\"'
    run_shell_cmd(cmd, imp_instance_path)

  def imp_fpga_app_flash(self, platform_name:str, app_name:str, target_imp_class:str, build_mode:str, imp_instance_path:Path):
    assert imp_instance_path.is_dir(), imp_instance_path
    #self.imp_fpga_build(platform_name, 'flash_server', target_imp_class, build_mode) # bug
    #self.imp_fpga_after_build(platform_name, 'flash_server', target_imp_class, build_mode, imp_instance_path)
    self.imp_fpga_build(platform_name, app_name, target_imp_class, build_mode)
    self.imp_fpga_after_build(platform_name, app_name, target_imp_class, build_mode, imp_instance_path)
    #
    assert (imp_instance_path/'program_flash_server.tcl').is_file(), '\"make flash_server\" first!'
    script = imp_instance_path / f'program_{app_name}.tcl'
    assert script.is_file(), script
    self.__prepare_ocd(imp_instance_path)
    cmd = self._get_fpga_run_cmd(target_imp_class, imp_instance_path)
    cmd += f' -c \"source {script}; exit\"'
    run_shell_cmd(cmd, imp_instance_path)
  
  def imp_fpga_gen_flash_script(self, platform_name:str, app_name:str, target_imp_class:str, imp_instance_path:Path):
    fpga_info_dict = self.imp_class.get_fpga_info(target_imp_class)

    template_file = self._get_env_file('xilinx', 'dump_flash_image.tcl.template')
    output_file = self._get_dump_flash_image_script_path(imp_instance_path)
    config_list = (('FLASH_IMAGE_FILENAME', str(self._get_flash_image_name(platform_name, app_name, target_imp_class, imp_instance_path))),)
    configure_template_file(template_file, output_file, config_list)

    template_file = self._get_env_file('xilinx', 'program_flash_image.tcl.template')
    output_file = self._get_program_flash_image_script_path(imp_instance_path)
    config_list = (('FLASH_IMAGE_FILENAME', str(self._get_flash_image_name(platform_name, app_name, target_imp_class, imp_instance_path))),
                   ('CFG_MEM', fpga_info_dict['cfg_mem']),
                   ('FLASH_INTERFACE_TYPE', fpga_info_dict['flash_interface_type']))
    configure_template_file(template_file, output_file, config_list)

  def imp_fpga___project(self, platform_name:str, target_imp_class:str, imp_instance_path:Path):
    self.imp_fpga_xci(platform_name, target_imp_class, imp_instance_path)
    self.imp_fpga_info(imp_instance_path)
    cmd = 'vivado -mode batch -source {0}'.format(self.devkit.get_devkit_path('xilinx','make_project.tcl'))
    run_shell_cmd(cmd, imp_instance_path, stdout=None, stderr=None, asserts_when_error=False)
  
  def imp_fpga_project(self, platform_name:str, target_imp_class:str, imp_instance_path:Path, runs_in_background=False):
    if self.devkit.is_called_by_gui or self.config.implements_fpga_in_terminal:
      cmd = 'make --no-print-directory __project'
      run_shell_cmd_with_terminal(cmd, imp_instance_path)
    else:
      self.imp_fpga___project(platform_name, target_imp_class, imp_instance_path)
  
  def imp_fpga_project_request(self, platform_name:str, target_imp_class:str, imp_instance_path:Path):
    self.imp_fpga_project(platform_name, target_imp_class, imp_instance_path, True)

  @staticmethod
  def imp_fpga_result_path(imp_instance_path:Path):
    return imp_instance_path / 'imp_result'

  @staticmethod
  def imp_fpga_imp_log(imp_instance_path:Path):
    return RvxWorkspace.imp_fpga_result_path(imp_instance_path) / 'vivado_imp.log'

  def imp_fpga_project_list(self, imp_instance_path:Path):
    result_path = RvxWorkspace.imp_fpga_result_path(imp_instance_path)
    return tuple(result_path.glob('*.xpr'))

  def imp_fpga_bit_list(self, imp_instance_path:Path):
    result_path = RvxWorkspace.imp_fpga_result_path(imp_instance_path)
    return tuple(result_path.glob('*.bit'))

  def imp_fpga_project_check(self, platform_name:str, imp_name:str):
    assert platform_name
    assert imp_name
    imp_instance_path = self._get_imp_path(platform_name, imp_name)
    result_path = RvxWorkspace.imp_fpga_result_path(imp_instance_path)
    status_list = ( \
                 ( False, result_path/'set_xdc', str(100)),
                 ( False, result_path/'syn_rtl', str(90)),
                 ( False, result_path/'syn_xci', str(60)),
                 ( False, result_path/'read_source', str(20)),
                 ( False, result_path/f'{platform_name}.xpr', str(10)),
                 ( False, None, 0)
           )
    self.__check_status(status_list)

  def imp_fpga_project_finalize(self, imp_instance_path:Path):
    return

  def imp_fpga_open_project(self, imp_instance_path:Path):
    result_path = RvxWorkspace.imp_fpga_result_path(imp_instance_path)
    xpr_list = tuple(result_path.glob('*.xpr'))
    if len(xpr_list)==0:
      print('Please make vivado project first!')
    elif len(xpr_list)>=2:
      print('Too many vivado project')
    else:
      run_shell_cmd_with_terminal(f'vivado {xpr_list[0]}', imp_instance_path)

  @staticmethod
  def get_app_log_path(general_log_path:Path, app_name:str) -> Path:
    app_log_path = general_log_path.parent / f'{general_log_path.stem}_{app_name}{general_log_path.suffix}'
    return app_log_path
  
  @staticmethod
  def backup_app_log(general_log_path:Path, app_name:str) -> None:
    copy_file(general_log_path, RvxWorkspace.get_app_log_path(general_log_path, app_name))
  
  def _imp_fpga_run_verify(self, platform_name:str, app_name:str, target_imp_class:str, build_mode:str, imp_instance_path:Path, printf_dump_path:Path) -> bool:
    printf_dump_path.unlink(missing_ok=True)
    self.imp_fpga_printf(target_imp_class, imp_instance_path)
    self.imp_fpga_run(platform_name, app_name, target_imp_class, build_mode, imp_instance_path)
    self.wait_app_finish_on_fpga(printf_dump_path)
    self.backup_app_log(printf_dump_path, app_name)
    
    result = self.get_app_return_from_log(printf_dump_path)
    if result:
      contents = f'\'{app_name}\' is verified'
    else:
      contents = f'\'{app_name}\' is NOT verified'
    self.devkit.handle_output(contents)
    return result
  
  def _imp_fpga_check_run_verify(self):
    assert self.config.printf_log_filename, f'Please set \`printf_log_filename\' in {self.config.tool_config_path}'

  def imp_fpga_run_verify(self, platform_name:str, app_name:str, target_imp_class:str, build_mode:str, imp_instance_path:Path) -> None:
    self._imp_fpga_check_run_verify()
    printf_dump_path = Path(self.config.printf_log_filename)
    self._imp_fpga_run_verify(platform_name, app_name, target_imp_class, build_mode, imp_instance_path, printf_dump_path)
  
  def imp_fpga_verify_apps(self, platform_name:str, target_imp_class:str, build_mode:str, imp_instance_path:Path):
    self._imp_fpga_check_run_verify()

    app_list = self.info_verifying_fpga_app_list(platform_name)
    contents = '\n'.join(app_list)
    self.devkit.handle_output(contents)

    for app_name in app_list:
      self.app_clean(platform_name, app_name, target_imp_class)
      self.imp_fpga_build(platform_name, app_name, target_imp_class, build_mode)
    
    printf_dump_path = Path(self.config.printf_log_filename)
    app_printf_dump_path = self.get_app_log_path(printf_dump_path, '*')
    remove_files(app_printf_dump_path.parent, app_printf_dump_path.name)

    result = True
    for app_name in app_list:
      result = self._imp_fpga_run_verify(platform_name, app_name, target_imp_class, build_mode, imp_instance_path, printf_dump_path)
      if not result:
        break
    
    self.kill_printf_if_exsit()
    if result:
      print ('All apps are verified')
  
  def imp_fpga_wait_app(self, platform_name:str, target_imp_class:str, build_mode:str, imp_instance_path:Path):
    assert self.config.printf_log_filename, f'Please set \`printf_log_filename\' in {self.config.tool_config_path}'
    printf_dump_path = Path(self.config.printf_log_filename)
    self.wait_app_finish_on_fpga(printf_dump_path)

  def kill_process_on_linux(self, process_name:str) -> None:
      assert is_linux
      cmd = make_cmd_sudo(f'pkill -9 {process_name}', self.devkit.get_sudo_passwd())
      run_shell_cmd(cmd, self.devkit_path)
      while is_process_running(process_name): time.sleep(1)
  
  def kill_process_if_exsit_on_linux(self, process_name:str) -> None:
    assert is_linux
    if is_process_running(process_name):
      kill_process_on_linux(process_name)

  def is_printf_running(self) -> bool:
    if is_linux:
      return is_process_running('minicom')
    # putty opened with -serial, same condition as kill_printf_if_exsit
    import base64
    ps_script = "$ProgressPreference='SilentlyContinue'; " \
                "@(Get-CimInstance Win32_Process -Filter \"Name='putty.exe'\" | Where-Object { $_.CommandLine -match '-serial' }).Count"
    encoded = base64.b64encode(ps_script.encode('utf-16-le')).decode()
    result = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-EncodedCommand', encoded], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, errors='replace')
    return result.stdout.strip() not in ('', '0')
  
  def kill_printf_if_exsit(self) -> None:
    if self.is_printf_running():
      if is_linux:
        self.kill_process_on_linux('minicom')
      else:
        # kill only putty opened with -serial (keeps ssh sessions), then wait until the COM port is released
        import base64
        ps_script = "$ProgressPreference='SilentlyContinue'; " \
                    "Get-CimInstance Win32_Process -Filter \"Name='putty.exe'\" | Where-Object { $_.CommandLine -match '-serial' } | " \
                    "ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Wait-Process -Id $_.ProcessId -ErrorAction SilentlyContinue }"
        encoded = base64.b64encode(ps_script.encode('utf-16-le')).decode()
        subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-EncodedCommand', encoded], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
  
  def kill_openocd_if_exsit(self) -> None:
    self.kill_process_if_exsit_on_linux('openocd_rvp')
  
  @staticmethod
  def wait_app_finish_on_fpga(log_path:Path) -> None:
    while 1:
      time.sleep(1)
      if not log_path.is_file():
        continue
      contents = log_path.read_text(encoding='utf8')
      if 'Assert Failed:' in contents:
        break
      elif '[RVX/END]'in contents:
        break
  
  @staticmethod
  def get_app_return_from_log(log_path:Path) -> bool:
    result = None
    assert log_path.is_file()
    contents = log_path.read_text(encoding='utf8')
    if 'Assert Failed:' in contents:
      result = False
    else:
      result = True
    return result

  def imp_fpga___imp(self, platform_name:str, target_imp_class:str, imp_instance_path:Path):
    vivado_imp_log = RvxWorkspace.imp_fpga_imp_log(imp_instance_path)
    remove_file(vivado_imp_log)
    self.imp_fpga_xci(platform_name, target_imp_class, imp_instance_path)
    self.imp_fpga_info(imp_instance_path)
    cmd = 'vivado -mode batch -source {0}'.format(self.devkit.get_devkit_path('xilinx','implement.tcl'))
    returncode = run_shell_cmd(cmd, imp_instance_path, stdout=None, stderr=None, asserts_when_error=False).returncode
    copy_file(imp_instance_path/'vivado.log', vivado_imp_log)
    copy_file(imp_instance_path/'set_path.tcl', RvxWorkspace.imp_fpga_result_path(imp_instance_path))
    copy_file(self.platform_file(platform_name), RvxWorkspace.imp_fpga_result_path(imp_instance_path))
    copy_directory(self._get_arch_path(platform_name), RvxWorkspace.imp_fpga_result_path(imp_instance_path) / self._get_arch_path(platform_name).name )
    self.imp_fpga_check_imp(imp_instance_path)    

  def imp_fpga_imp(self, platform_name:str, target_imp_class:str, imp_instance_path:Path):
    if self.devkit.is_called_by_gui or self.config.implements_fpga_in_terminal:
      cmd = 'make --no-print-directory __imp'
      run_shell_cmd_with_terminal(cmd, imp_instance_path)
    else:
      self.imp_fpga___imp(platform_name, target_imp_class, imp_instance_path)

  def imp_fpga_imp_request(self, imp_instance_path:Path):
    self.imp_fpga_imp(imp_instance_path)
  
  def imp_fpga_imp_check(self, platform_name:str, imp_instance_path:Path):
    result_path = RvxWorkspace.imp_fpga_result_path(imp_instance_path)
    status_list = ( \
                 ( False, result_path/'gen_bit', str(100)),
                 ( False, result_path/'route_top', str(90)),
                 ( False, result_path/'place_top', str(70)),
                 ( False, result_path/'syn_top', str(50)),
                 ( False, result_path/'set_cdc', str(30)),
                 ( False, result_path/'syn_xci', str(15)),
                 ( False, result_path/f'{platform_name}.xpr', str(5)),
                 ( False, None, 0)
           )
    self.__check_status(status_list)

  def imp_fpga_reimp(self, platform_name:str, target_imp_class:str, imp_instance_path:Path):
    for bit_file in self.imp_fpga_bit_list(imp_instance_path):
      remove_file(bit_file)
    self.imp_fpga_imp(platform_name, target_imp_class, imp_instance_path)

  def __log_error(self, job_name:str, log:str):
    self.devkit.add_new_job(job_name, True, 'start')
    self.devkit.add_log(log, 'error', is_user=True)
    self.devkit.check_log()

  def imp_fpga_check_imp(self, imp_instance_path:Path):
    result_path = RvxWorkspace.imp_fpga_result_path(imp_instance_path)
    log_list = []

    num_bit_file = len(self.imp_fpga_bit_list(imp_instance_path))
    if num_bit_file==1:
      bit_result = 'Generated'
    elif num_bit_file==0:
      bit_result = 'Fail'
    else:
      bit_result = 'Bug'
    log_list.append(f'Bit: {bit_result}')

    vivado_imp_log = RvxWorkspace.imp_fpga_imp_log(imp_instance_path)
    if vivado_imp_log.is_file():
      analyze_vivado_log_file = self._get_env_file('util', 'analyze_vivado_log.py')
      cmd = f'{self.config.python3_cmd} {analyze_vivado_log_file} -i {vivado_imp_log} -o {result_path} -op all'
      run_shell_cmd(cmd,result_path)

    timing_report_file = RvxWorkspace.imp_fpga_result_path(imp_instance_path) / 'route_timing_summary.rpt'
    if bit_result!='Generated':
      timing_result = 'N/A'
    elif not timing_report_file.is_file():
      timing_result = f'Bug (Absence of {timing_report_file.relative_to(imp_instance_path)})'
    else:
      contents = timing_report_file.read_text(encoding='utf8')
      if 'Slack (VIOLATED)' in contents:
        timing_result = f'Fail (VIOLATED in {timing_report_file.relative_to(imp_instance_path)})'
      else:
        timing_result = 'Success'
    log_list.append(f'Timing: {timing_result}')
    
    if vivado_imp_log.is_file():
      contents = vivado_imp_log.read_text(encoding='utf8')
      check_phrase_list = ['DRC RTSTAT-10']
      for phrase in check_phrase_list:
        if phrase in contents:
          log_list.append(f'Suspicious: {phrase}')

    self.devkit.add_new_job('imp_fpga_check_imp', True, 'start')
    self.devkit.add_log('\n'.join(log_list), 'done' if bit_result=='Generated' else 'error', is_user=True)
    self.devkit.check_log(True)

  def imp_fpga_imp_finalize(self, imp_instance_path:Path):
    return

  def imp_fpga_program(self, platform_name:str, target_imp_class:str, imp_instance_path:Path):
    if not self.imp_fpga_set_path_path(imp_instance_path).is_file():
      self.imp_fpga_path(platform_name, target_imp_class, imp_instance_path)
    if len(self.imp_fpga_bit_list(imp_instance_path))!=1:
      self.__log_error('imp_fpga_program', 'Bitstream is NOT found. Run "make imp" first')
    self.kill_printf_if_exsit()
    result = run_shell_cmd('vivado -mode batch -source {0}'.format(self.devkit.get_devkit_path('xilinx','program_fpga.tcl')),imp_instance_path, stdout=None, stderr=None, asserts_when_error=False)
    if result.returncode!=0:
      self.__log_error('imp_fpga_program', 'Programming FPGA failed. See vivado.log')
  def imp_fpga_mcs(self, imp_instance_path:Path):
    run_shell_cmd('vivado -mode batch -source ./gen_mcs.tcl',imp_instance_path, stdout=None, stderr=None, asserts_when_error=False)
  def imp_fpga_program_flash(self, platform_name:str, target_imp_class:str, imp_instance_path:Path):
    if not self.imp_fpga_set_path_path(imp_instance_path).is_file():
      self.imp_fpga_path(platform_name, target_imp_class, imp_instance_path)
    self.kill_printf_if_exsit()
    result = run_shell_cmd('vivado -mode batch -source {0}'.format(self.devkit.get_devkit_path('xilinx','program_fpga_flash.tcl')),imp_instance_path, stdout=None, stderr=None, asserts_when_error=False)
    if result.returncode!=0:
      self.__log_error('imp_fpga_program_flash', 'Programming flash failed. See vivado.log')

  def __get_ila_result_path(self, imp_instance_path:Path):
    return imp_instance_path / 'ila'

  def imp_fpga_ila(self, platform_name:str, target_imp_class:str, imp_instance_path:Path):
    fpga_info_dict = self.imp_class.get_fpga_info(target_imp_class)
    self.imp_fpga_ila_clean(imp_instance_path)
    ila_result_path = self.__get_ila_result_path(imp_instance_path)
    if not ila_result_path.is_dir():
      ila_result_path.mkdir()

    ila_signal_path_list = []
    ila_signal_path_list += list((self._get_platform_path(platform_name)/'user'/'ila'/'common').glob('*.xml'))
    ila_signal_path_list += list((self._get_platform_path(platform_name)/'user'/'ila'/target_imp_class).glob('*.xml'))
    
    verilog_text = ''
    tcl_text = ''
    for input_file in ila_signal_path_list:
      xml_tree = parse(str(input_file))
      xml_root = xml_tree.getroot()
      assert xml_root.tag=='rvx', xml_root.tag
      for ila_xml in xml_root.findall('ila'):
        ila = RvxIla(ila_xml)
        verilog_text += ila.generate_verilog()
        tcl_text += ila.generate_tcl(ila_result_path, fpga_info_dict['part'])

    ila_output_file = ila_result_path / 'ila_description.vh'
    ila_output_file.write_text(verilog_text, encoding='utf8')
    ila_generating_file = ila_result_path / 'generate_ila.tcl'
    ila_generating_file.write_text(tcl_text, encoding='utf8')

  def imp_fpga_ila_clean(self, imp_instance_path:Path):
    ila_result_path = self.__get_ila_result_path(imp_instance_path)
    remove_directory(ila_result_path)

  def imp_fpga_printf(self, target_imp_class:str, imp_instance_path:Path, asserts_when_error=True):
    self.kill_printf_if_exsit()
    imp_dict = self.imp_class.get_imp_class_info(target_imp_class)
    if is_linux:
      usb2uart = imp_dict['usb2uart']
      vendor, product, interface_number = usb2uart.split(':')
      target_ttyusb = None
      run_shell_cmd(make_cmd_sudo('modprobe ftdi_sio', self.devkit.get_sudo_passwd()), imp_instance_path)
      cmd = make_cmd_sudo(f'modprobe ftdi_sio vendor=0x{vendor} product=0x{product}; sleep 0.5', self.devkit.get_sudo_passwd())
      run_shell_cmd(cmd, imp_instance_path)
      for ttyusb in Path('/dev').glob('ttyUSB*'):
        ttyusb_info = run_shell_cmd(f'udevadm info -a -n {ttyusb}').stdout
        if f'ATTRS{{idVendor}}==\"{vendor}\"' not in ttyusb_info:
          continue
        if f'ATTRS{{idProduct}}==\"{product}\"' not in ttyusb_info:
          continue
        if f'ATTRS{{bInterfaceNumber}}==\"{interface_number}\"' not in ttyusb_info:
          continue
        target_ttyusb = ttyusb
        break
      if asserts_when_error:
        assert target_ttyusb
      if self.config.printf_log_filename:
        minicom_output_path = Path(self.config.printf_log_filename).absolute()
        minicom_output_path.unlink(missing_ok=True)
        cmd = f'minicom -D {target_ttyusb} -C {minicom_output_path}'
      else:
        cmd = f'minicom -D {target_ttyusb}'
      cmd = make_cmd_sudo(cmd, self.devkit.get_sudo_passwd())
      if self.devkit.is_called_by_gui or self.config.shows_printf_in_terminal:
        run_shell_cmd_with_terminal(cmd, imp_instance_path)
      else:
        run_shell_cmd(cmd, imp_instance_path, asserts_when_error=asserts_when_error)
    else:
      com_port = os.environ.get('RVX_UART_PORT')
      if not com_port:
        vendor, product, interface_number = imp_dict['usb2uart'].split(':')
        candidates = self.find_windows_com_ports(vendor, product, int(interface_number, 16))
        if candidates:
          com_port = candidates[0]
          if len(candidates) > 1:
            print(f'[RVX] multiple usb2uart ports found: {candidates}, using {com_port} (set RVX_UART_PORT to override)')
        else:
          print(f'[RVX] no COM port for usb2uart {imp_dict["usb2uart"]}. available: {self.find_windows_com_ports()}')
          print('[RVX] set RVX_UART_PORT (e.g. COM6) to select the port manually')
          if asserts_when_error:
            assert com_port, 'usb2uart not found'
          run_shell_cmd('start devmgmt.msc', stdout=None, stderr=None)
          run_shell_cmd('start putty.exe', stdout=None, stderr=None)
          return
      print(f'[RVX] usb2uart -> {com_port}')
      cmd = f'putty.exe -serial {com_port} -sercfg 115200,8,n,1,N'
      if self.config.printf_log_filename:
        cmd += f' -sessionlog "{Path(self.config.printf_log_filename).absolute()}" -logoverwrite'
      # detach putty without inheriting stdout/stderr, otherwise a caller reading make's output waits until putty closes
      subprocess.Popen(cmd, cwd=imp_instance_path, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       close_fds=True, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)

  @staticmethod
  def find_windows_com_ports(vendor:str=None, product:str=None, interface_number:int=None) -> list:
    # returns active COM ports matching the given USB vid/pid/interface (all active ports if vendor is None)
    import winreg
    import re
    def subkeys(key):
      i = 0
      while True:
        try:
          yield winreg.EnumKey(key, i)
        except OSError:
          return
        i += 1
    def read_value(path, name):
      try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
          return winreg.QueryValueEx(key, name)[0]
      except OSError:
        return None
    active_ports = set()
    try:
      with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'HARDWARE\DEVICEMAP\SERIALCOMM') as key:
        i = 0
        while True:
          try:
            active_ports.add(winreg.EnumValue(key, i)[1])
          except OSError:
            break
          i += 1
    except OSError:
      return []
    if vendor is None:
      return sorted(active_ports)
    matched = []
    # FTDI VCP driver: FTDIBUS\VID_0403+PID_6011+<serial><A|B|C|D>, suffix letter gives the interface
    # USB CDC/other: USB\VID_xxxx&PID_xxxx&MI_xx
    for bus in ('FTDIBUS', 'USB'):
      bus_path = rf'SYSTEM\CurrentControlSet\Enum\{bus}'
      try:
        bus_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, bus_path)
      except OSError:
        continue
      with bus_key:
        for dev_id in subkeys(bus_key):
          m = re.match(r'VID_([0-9A-Fa-f]{4})[+&]PID_([0-9A-Fa-f]{4})(?:[+&](.*))?$', dev_id)
          if not m or m.group(1).lower()!=vendor.lower() or m.group(2).lower()!=product.lower():
            continue
          rest = m.group(3) or ''
          if bus=='FTDIBUS':
            # only multi-interface chips (FT2232/FT4232) get the A~D suffix
            serial = rest.split('+')[0]
            suffix = serial[-1:]
            is_multi_interface = product.lower() in ('6010', '6011', '6048')
            dev_interface = ord(suffix)-ord('A') if is_multi_interface and suffix and suffix in 'ABCD' else 0
          else:
            mi = re.match(r'MI_([0-9A-Fa-f]{2})', rest)
            dev_interface = int(mi.group(1), 16) if mi else 0
          if interface_number is not None and dev_interface!=interface_number:
            continue
          with winreg.OpenKey(bus_key, dev_id) as dev_key:
            for inst in subkeys(dev_key):
              port = read_value(rf'{bus_path}\{dev_id}\{inst}\Device Parameters', 'PortName')
              if port and port in active_ports and port not in matched:
                matched.append(port)
    return sorted(matched, key=lambda x: int(re.sub(r'\D', '', x) or 0))

  def imp_fpga_manual_top(self, platform_name:str, target_imp_class:str, imp_instance_path:Path):
    self.platform_user(platform_name)
    target_path = self._get_user_path(platform_name) / 'fpga' / target_imp_class / 'set_top_module.tcl'
    if not target_path.parent.is_dir():
      target_path.parent.mkdir(parents=True)
    copy_file(self._get_env_file('xilinx', 'set_top_module.tcl'), target_path)
    source_path = target_path.parent / 'src'
    print(f'Locate your own top file at {source_path}')
    print(f'Specify your top module name at {target_path}')
    print(f'{platform_name.upper()}_FPGA is NOT allowed for your module name')

  def __prepare_ocd(self, imp_instance_path:Path):
    if is_linux:
      self.kill_openocd_if_exsit()
      cmd = 'rmmod ftdi_sio'
      cmd = make_cmd_sudo(cmd, self.devkit.get_sudo_passwd())
      run_shell_cmd(cmd, imp_instance_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, prints_when_error=False, asserts_when_error=False)
  
  def _get_fpga_run_cmd(self, target_imp_class:str, imp_instance_path:Path):
    ocd_cfg_file = imp_instance_path / f'{target_imp_class}.cfg'
    cmd = f'{self.config.ocd_binary_file} -f {ocd_cfg_file}'
    if is_linux:
      cmd = make_cmd_sudo(cmd, self.devkit.get_sudo_passwd())
    return cmd

  def imp_fpga_run_ocd(self, target_imp_class:str, imp_instance_path:Path):
    self.__prepare_ocd(imp_instance_path)
    if self.devkit.is_called_by_gui or self.config.runs_ocd_in_terminal:
      run_shell_cmd_with_terminal(self._get_fpga_run_cmd(target_imp_class,imp_instance_path), imp_instance_path)
    else:
      run_shell_cmd(self._get_fpga_run_cmd(target_imp_class,imp_instance_path), imp_instance_path)

  def imp_fpga_connect_ocd(self, imp_instance_path:Path):
    if self.devkit.is_called_by_gui or self.config.connects_ocd_in_terminal:
      run_shell_cmd_with_terminal('telnet localhost 4444', imp_instance_path)
    else:
      run_shell_cmd('telnet localhost 4444', imp_instance_path)
    
  @staticmethod
  def dump_type_path(dump_dir:Path):
    return dump_dir / 'dump_type.txt'
  
  @staticmethod
  def dump_data_path(dump_dir:Path):
    return dump_dir / 'dump_data.bin'
  
  def uncompress_dump(self, imp_path:Path):
    dump_dir = imp_path / 'dump'
    dump_type_path = self.dump_type_path(dump_dir)
    dump_data_path = self.dump_data_path(dump_dir)

    if dump_type_path.is_file():
      assert dump_data_path.is_file(), dump_data_path

      # read dump_type
      dump_type = int(dump_type_path.read_text(encoding='utf8'))
      dump_type_dict = {0:'MEMORY_DUMP_NONE',
                        1:'MEMORY_DUMP_FAKEFILE',
                        2:'MEMORY_DUMP_IMAGE'}
      print(f'dump type: {dump_type_dict[dump_type]}')
      if dump_type==0:
        pass
      elif dump_type==1:
        # split
        split_fakefiles_file = self._get_env_file('util', 'split_fakefiles.py')
        cmd = f'{self.config.python3_cmd} {split_fakefiles_file} -i {dump_data_path} -o {dump_dir}'
        result = run_shell_cmd(cmd,imp_path)
        print(result.stdout)
      elif dump_type==2:
        image_file = self.devkit.output_file
        if not image_file:
          image_file = dump_dir / 'dumped_image.jpg'
        copy_file(dump_data_path, image_file)
        print(f'Check {image_file.relative_to(imp_path)}')
      else:
          assert 0

  def imp_fpga_dump(self, target_imp_class:str, imp_instance_path:Path):
    dump_dir = imp_instance_path / 'dump'
    if dump_dir.is_dir():
      remove_directory(dump_dir)
    dump_dir.mkdir()

    dump_type_path = self.dump_type_path(dump_dir)
    dump_data_path = self.dump_data_path(dump_dir)

    # script
    template_file = self._get_env_file('ocd', 'dump_memory.tcl.template')
    script_file = imp_instance_path / template_file.stem
    config_list = (('TYPE_FILE',str(PurePosixPath(dump_type_path))),
                  ('DATA_FILE',str(PurePosixPath(dump_data_path))),)
    configure_template_file(template_file, script_file, config_list)

    # dump
    self.__prepare_ocd(imp_instance_path)
    cmd = self._get_fpga_run_cmd(target_imp_class, imp_instance_path)
    cmd += f' -c \"source {PurePosixPath(script_file)}; exit\"'
    run_shell_cmd(cmd, imp_instance_path)

    if is_linux:
      cmd = make_cmd_sudo(f'chown {script_file.owner()}:{script_file.group()} {dump_type_path} {dump_data_path}', self.devkit.get_sudo_passwd())
      run_shell_cmd(cmd, imp_instance_path)

    #
    self.uncompress_dump(imp_instance_path)

  def imp_fpga_dump_flash_image(self, platform_name:str, target_imp_class:str, imp_instance_path:Path):
    if not self.imp_fpga_set_path_path(imp_instance_path).is_file():
      self.imp_fpga_path(platform_name, target_imp_class, imp_instance_path)
    dump_flash_image_script_path = self._get_dump_flash_image_script_path(imp_instance_path)
    assert dump_flash_image_script_path.is_file()
    run_shell_cmd('vivado -mode batch -source {0}'.format(dump_flash_image_script_path),imp_instance_path, stdout=None, stderr=None, asserts_when_error=False)

    
  def imp_fpga_check_dumped_image(self, target_imp_class:str, imp_instance_path:Path):
    dump_dir = imp_instance_path / 'dump'
    for image_file in chain(dump_dir.glob('*.jpg'),dump_dir.glob('*.bmp')):
      if is_linux:
        cmd = f'display {image_file}'
      else:
        cmd = str(image_file)
      run_shell_cmd(cmd, imp_instance_path)
