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

import os
import getpass

from pathlib import Path

from rvx_engine_util import *
from rvx_config import *
from rvx_engine_log import *

import import_util
from generate_git_info import *

class RvxDevkit():
  @staticmethod
  def set_if_env_exist(variable_name):
    x = os.environ.get(variable_name)
    if x:
      x = Path(x)
      if not x.is_dir():
        x = None
    return x

  def __init__(self, config:RvxConfig, output_file:str, engine_log:RvxEngineLog, is_called_by_gui:bool):
    self.config = config
    self.output_file = Path(output_file).resolve() if output_file else None
    self.engine_log = engine_log
    self.is_called_by_gui = is_called_by_gui
    self.is_debug_mode = (self.config.home_path / 'debug').is_file()
    if self.is_debug_mode:
      print('Debug On!')

  def get_devkit_path(self, *args):
    return self.config.devkit_path.joinpath(*args)
  
  @property
  def get_imp_class_list_common_file(self):
    return self.get_devkit_path('info','rvx_imp_class_common.xml')

  def set_gitignore(self, type:str, path:Path):
    dst_file = path / '.gitignore'
    if not dst_file.exists():
      src_file = self.get_devkit_path('git',f'gitignore.{type}.txt')
      assert src_file.is_file()
      copy_file(src_file, dst_file)
    
  def geneate_rvx_each_template(self, type:str, path:Path):
    dst_file = path / 'rvx_each.mh'
    if not dst_file.exists():
      src_file = self.get_devkit_path('rvx_each',f'rvx_each.{type}.txt')
      assert src_file.is_file()
      copy_file(src_file, dst_file)

  def handle_output(self, contents:str):
    if self.output_file:
      with open(self.output_file,'w') as f:
        f.write(contents)
    else:
      print(contents)

  # sudo asks the password by itself
  def get_sudo_passwd(self):
    return None

  def add_new_job(self, job_name:str, is_local:bool, job_status:str=None):
    self.engine_log.add_new_job(job_name, is_local, job_status)

  def add_log(self, log:str, status:str=None, is_file:bool=False, is_user:bool=False):
    self.engine_log.add_log(log, is_file=is_file, is_user=is_user)
    if status!=None:
      self.engine_log.set_status(status)

  def add_process_log(self, log:subprocess.CompletedProcess, is_user:bool):
    if log.stderr:
      contents = ''
      if log.stdout:
        contents += log.stdout
        contents += '\n'
      contents += log.stderr
      self.engine_log.add_log(contents, is_file=True, is_user=True)
      self.engine_log.set_status('fail')
    else:
      if log.stdout:
        self.engine_log.add_log(log.stdout, is_file=True, is_user=True)
      self.engine_log.set_status('done')

  def check_log(self, prints_if_local:bool=False):
    self.engine_log.export_file()
    status = self.engine_log.current_job.status
    if status=='error' or status=='fail':
      print(self.engine_log.current_job)
      if status=='error':
        exit(11)
      else:
        exit(21)
    else:
      if prints_if_local:
        print(self.engine_log.current_job)

  def home_git_info(self):
    git_version = get_git_version(self.config.home_path)
    return git_version
  
  def home_git_name(self):
    git_name = get_git_name(self.config.home_path)
    return git_name

  def devkit_git_info(self):
    return get_git_version(self.config.devkit_path)

  def rvx_version(self):
    return f'{self.home_git_info()} ({get_git_date(self.config.home_path)})'

  def username(self):
    return getpass.getuser()
