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
## 2019-04-15
## Kyuseung Han (han@etri.re.kr)
## ****************************************************************************
## ****************************************************************************

import argparse
import os
import platform

from rvx_engine_util import *
from rvx_config import *
from rvx_devkit import *
from rvx_workspace import *
from rvx_engine_log import *

import import_util

if __name__ == '__main__':
  # argument
  parser = argparse.ArgumentParser(description='RVX Engine')
  parser.add_argument('-workspace', '-ws', help='workspace directory')
  parser.add_argument('-platform', '-p', help='platform')
  parser.add_argument('-target_imp_class', '-tic', help='target imp class')
  parser.add_argument('-app', '-a', help='app')
  parser.add_argument('-cmd', '-c', help='command')
  parser.add_argument('-input', '-i', help='input file name')
  parser.add_argument('-output', '-o', help='output file name')
  parser.add_argument('-build_mode', '-bm', help='build mode')
  parser.add_argument('-imp_dir', help='implementation directory')
  parser.add_argument('-log', help='log directory')
  parser.add_argument('--gui', action="store_true", help='if called by gui')
  args = parser.parse_args()

  assert is_centos or is_ubuntu or is_windows, 'NOT supported OS'
  
  curdir = Path('.').resolve()

  assert args.cmd

  workspace = Path(args.workspace).resolve()
  assert workspace.is_dir(), args.workspace
  platform_name = args.platform
  app_name = args.app
  
  if args.imp_dir:
    imp_instance_path = Path(args.imp_dir).resolve()
  else:
    imp_instance_path = None
    
  home_path = os.environ.get('RVX_RELEASE_HOME')
  if home_path:
    home_path = Path(home_path)
  else:
    home_path = workspace.parent
  config = RvxConfig(home_path)
  engine_log = RvxEngineLog(args.log)
  engine_log.clean()
  engine_log.add_new_job('logfile_setup', True, 'done')
  devkit = RvxDevkit(config, args.output, engine_log, args.gui)
  cmd_list = args.cmd.split('.')
  is_cmd_not_related_to_workspace = False

  # command not related to workspace
  if False:
    pass
  
  elif cmd_list[1]=='engine_check':
    is_cmd_not_related_to_workspace = True
    config.tool_config.export_file()
  
  elif cmd_list[0]=='gui':
    is_cmd_not_related_to_workspace = True
    if False:
      pass
    elif cmd_list[1]=='cmd':
      run_shell_cmd_with_terminal(cmd='make --no-print-directory _open_gui_cmd', cwd=imp_instance_path)
    elif cmd_list[1]=='cmdadv':
      run_shell_cmd_with_terminal(cmd='make --no-print-directory _open_gui_cmd_adv', cwd=imp_instance_path)
    elif cmd_list[1]=='run':
      run_shell_cmd_with_terminal(cmd='make --no-print-directory _open_gui_run', cwd=imp_instance_path)
    else:
      assert 0, cmd_list
  
  elif cmd_list[1]=='run_gui':
    is_cmd_not_related_to_workspace = True
    #execute_shell_cmd(cmd='make gui.run', cwd=imp_instance_path, runs_in_background=True)
    run_shell_cmd_with_terminal(cmd='make gui.run', cwd=imp_instance_path)
  
  elif cmd_list[1].startswith('gitadd'):
    is_cmd_not_related_to_workspace = True
    recursively = '_rc' in cmd_list[1]
    cmd  = 'make --no-print-directory _gitadd'
    cmd += f' _RVX_HOME={workspace.parent}'
    if recursively:
      cmd += f' _IS_RECURSIVELY=\"--recursively\"'
    else:
      cmd += f' _IS_RECURSIVELY=\"\"'
    
    run_shell_cmd(cmd=cmd, cwd=curdir, stdout=None, stderr=None, asserts_when_error=False)
    #run_shell_cmd(cmd=cmd, cwd=curdir)
    #result = run_shell_cmd(cmd=cmd, cwd=curdir)
    #devkit.handle_output(result.stdout)

  elif cmd_list[1]=='gitignore':
    is_cmd_not_related_to_workspace = True
    devkit.set_gitignore(cmd_list[0], Path('.'))
  
  elif cmd_list[1]=='rvx_each':
    is_cmd_not_related_to_workspace = True
    devkit.geneate_rvx_each_template(cmd_list[0], Path('.'))

  elif cmd_list[1]=='is_debug_mode':
    is_cmd_not_related_to_workspace = True
    devkit.handle_output(str(False))

  elif cmd_list[1]=='tool_config_path':
    is_cmd_not_related_to_workspace = True
    devkit.handle_output(str(config.tool_config_path))

  elif cmd_list[1]=='devkit_git_info':
    is_cmd_not_related_to_workspace = True
    contents = devkit.devkit_git_info()
    devkit.handle_output(contents)

  elif cmd_list[1]=='rvx_version':
    is_cmd_not_related_to_workspace = True
    contents = devkit.rvx_version()
    devkit.handle_output(contents)

  elif cmd_list[1]=='home_git_info':
    is_cmd_not_related_to_workspace = True
    contents = devkit.home_git_info()
    devkit.handle_output(contents)

  if is_cmd_not_related_to_workspace:
    exit()
  
  # command related to workspace
  engine_log.export_file()
  config.tool_config.export_file()
  rvx_workspace = RvxWorkspace(devkit, workspace, platform_name)

  if False:
    pass

  elif cmd_list[0]=='home' or cmd_list[0]=='info':
    if False:
      pass
    elif cmd_list[1]=='platform_list':
      contents = '\n'.join(rvx_workspace.info_platform_list())
      devkit.handle_output(contents)

    elif cmd_list[1]=='app_list':
      rvx_workspace.print_app_list(platform_name)

    elif cmd_list[1]=='app_path':
      contents = rvx_workspace.app_path(platform_name, app_name)
      devkit.handle_output(str(contents))

    elif cmd_list[1]=='fpga_list':
      contents = '\n'.join(rvx_workspace.info_fpga_list())
      devkit.handle_output(contents)

    elif cmd_list[1]=='imp_class_list':
      contents = '\n'.join(rvx_workspace.info_imp_class_list())
      devkit.handle_output(contents)

    elif cmd_list[1]=='imp_instance_list':
      contents = '\n'.join([ f'{x}:{y}:{z}' for x, y, z in rvx_workspace.info_imp_instance_list(platform_name)])
      devkit.handle_output(contents)

    elif cmd_list[1]=='fpga_instance_list':
      contents = '\n'.join([ f'{x}:{y}:{z}' for x, y, z in rvx_workspace.info_fpga_instance_list(platform_name)])
      devkit.handle_output(contents)

    elif cmd_list[1]=='platform_file':
      contents = rvx_workspace.platform_file(platform_name)
      devkit.handle_output(str(contents))
  
    elif cmd_list[1]=='localize':
      for imp_path in config.home_path.glob('**/imp_*'):
        if imp_path.is_dir():
          if imp_path.name.startswith('imp_') and '_20' in imp_path.name:
            print(imp_path)
            run_shell_cmd('make path', imp_path)

    else:
      assert 0, cmd_list

  elif cmd_list[0]=='platform':
    if False:
      pass
    elif cmd_list[1]=='platform_list':
      contents = '\n'.join(rvx_workspace.info_platform_list())
      devkit.handle_output(contents)
    elif cmd_list[1]=='freeze':
      rvx_workspace.platform_freeze(platform_name)
    elif cmd_list[1]=='unfreeze':
      rvx_workspace.platform_unfreeze(platform_name)
    elif cmd_list[1]=='clean':
      rvx_workspace.platform_clean(platform_name)
    elif cmd_list[1]=='clean_all_imp' or cmd_list[1]=='clean_imp':
      rvx_workspace.platform_clean_all_imp(platform_name)
    elif cmd_list[1]=='distclean':
      rvx_workspace.platform_distclean(platform_name)
    elif cmd_list[1]=='import':
      rvx_workspace.platform_import(platform_name)
    elif cmd_list[1]=='testbench':
      rvx_workspace.platform_testbench(platform_name)
    elif cmd_list[1]=='app_base':
      rvx_workspace.platform_app_base(platform_name)
    elif cmd_list[1]=='system_app':
      rvx_workspace.platform_system_app(platform_name)
    elif cmd_list[1]=='user':
      rvx_workspace.platform_user(platform_name)
    elif cmd_list[1]=='util':
      rvx_workspace.platform_util(platform_name)
    elif cmd_list[1]=='new':
      rvx_workspace.platform_new(platform_name)
    elif cmd_list[1]=='delete':
      rvx_workspace.platform_delete(platform_name)
    elif cmd_list[1]=='syn_arch':
      rvx_workspace.platform_syn_arch(platform_name)
    elif cmd_list[1]=='syn':
      if len(cmd_list)==2:
        rvx_workspace.platform_syn(platform_name)
      else:
        assert 0, cmd_list
    elif cmd_list[1]=='sim_rtl':
      rvx_workspace.platform_sim_rtl(platform_name)
    elif cmd_list[1]=='sim_rtl_syn':
      rvx_workspace.platform_sim_rtl_syn(platform_name)
    elif cmd_list[1]=='imp_fpga' or cmd_list[1]=='fpga':
      rvx_workspace.platform_imp_fpga(platform_name, args.target_imp_class, imp_instance_path)
    elif cmd_list[1]=='imp_chip':
      rvx_workspace.platform_imp_chip(platform_name, args.target_imp_class, imp_instance_path)
    elif cmd_list[1]=='imp_fpga_dir':
      rvx_workspace.platform_imp_fpga_dir(platform_name, args.target_imp_class, imp_instance_path)

    elif cmd_list[1]=='app_list':
      rvx_workspace.print_app_list(platform_name)
    elif cmd_list[1]=='fpga_list':
      contents = '\n'.join(rvx_workspace.info_fpga_list())
      devkit.handle_output(contents)
    else:
      assert 0, cmd_list

  elif cmd_list[0]=='app':
    if False:
      pass
    elif cmd_list[1]=='build_dir':
      rvx_workspace.app_build_dir(platform_name, app_name, args.target_imp_class, args.build_mode)

    elif cmd_list[1]=='compile_list':
      rvx_workspace.app_compile_list(platform_name, app_name)
  
    elif cmd_list[1]=='compile':
      rvx_workspace.app_compile(platform_name, app_name, args.target_imp_class, args.build_mode, False)

    elif cmd_list[1]=='compile_incremental':
      rvx_workspace.app_compile(platform_name, app_name, args.target_imp_class, args.build_mode, True)

    elif cmd_list[1]=='build':
      rvx_workspace.app_build(platform_name, app_name, args.target_imp_class, args.build_mode)

    elif cmd_list[1]=='clean':
      rvx_workspace.app_clean(platform_name, app_name, args.target_imp_class)

    elif cmd_list[1]=='new':
      rvx_workspace.app_new(platform_name, app_name)

    elif cmd_list[1]=='delete':
      rvx_workspace.app_delete(platform_name, app_name)
    
    else:
      assert 0, cmd_list
  
  elif cmd_list[0]=='sim_rtl':
    if False:
      pass
    elif cmd_list[1]=='path':
      rvx_workspace.sim_rtl_path(platform_name, imp_instance_path)
    elif cmd_list[1]=='script':
      rvx_workspace.sim_rtl_script(platform_name, imp_instance_path)
    elif cmd_list[1]=='build':
      rvx_workspace.sim_rtl_build(platform_name, app_name, args.build_mode)
    elif cmd_list[1]=='clean_build':
      rvx_workspace.sim_rtl_clean_build(platform_name, app_name, args.build_mode, imp_instance_path)
    elif cmd_list[1]=='after_build':
      rvx_workspace.sim_rtl_after_build(platform_name, app_name, args.build_mode, imp_instance_path)
    elif cmd_list[1]=='compile_test':
      rvx_workspace.sim_rtl_compile_test(platform_name, imp_instance_path)
    elif cmd_list[1]=='compile_test_all':
      rvx_workspace.sim_rtl_compile_test_all(platform_name, imp_instance_path)
    elif cmd_list[1]=='compile_rtl_normal':
      rvx_workspace.sim_rtl_compile_rtl_normal(platform_name, imp_instance_path)
    elif cmd_list[1]=='compile_rtl_debug':
      rvx_workspace.sim_rtl_compile_rtl_debug(platform_name, imp_instance_path)
    elif cmd_list[1]=='compile_rtl_debug_init':
      rvx_workspace.sim_rtl_compile_rtl_debug_init(platform_name, imp_instance_path)

    elif cmd_list[1]=='run_rtl':
      rvx_workspace.sim_rtl_run_rtl(platform_name, imp_instance_path)
    elif cmd_list[1]=='debug_rtl':
      rvx_workspace.sim_rtl_debug_rtl(platform_name, imp_instance_path)
    elif cmd_list[1]=='run':
      rvx_workspace.sim_rtl_run(platform_name, app_name, args.build_mode, imp_instance_path)
    elif cmd_list[1]=='run_verify':
      rvx_workspace.sim_rtl_run_verify(platform_name, app_name, args.build_mode, imp_instance_path)
    elif cmd_list[1]=='debug':
      rvx_workspace.sim_rtl_debug(platform_name, app_name, args.build_mode, imp_instance_path)
    elif cmd_list[1]=='debug_init':
      rvx_workspace.sim_rtl_debug_init(platform_name, app_name, args.build_mode, imp_instance_path)
    elif cmd_list[1]=='debug_view':
      rvx_workspace.sim_rtl_debug_view(platform_name, app_name, args.build_mode, imp_instance_path)
    elif cmd_list[1]=='view':
      rvx_workspace.sim_rtl_view(platform_name, imp_instance_path)

    elif cmd_list[1]=='compile_check':
      rvx_workspace.sim_rtl_compile_check(platform_name, imp_instance_path)
    elif cmd_list[1]=='verify_apps':
      rvx_workspace.sim_rtl_verify_apps(platform_name, args.build_mode, imp_instance_path)
    elif cmd_list[1]=='app_list':
      rvx_workspace.print_app_list(platform_name)
      rvx_workspace.gen_app_list(platform_name, imp_instance_path)
    else:
      assert 0, cmd_list

  elif cmd_list[0]=='imp_soc':
    if False:
      pass
    elif cmd_list[1]=='env':
      rvx_workspace.imp_chip_env(platform_name, args.target_imp_class)

  elif cmd_list[0]=='imp_fpga':
    if False:
      pass
    elif cmd_list[1]=='module':
      rvx_workspace.imp_fpga_module(platform_name, args.target_imp_class, imp_instance_path)
    elif cmd_list[1]=='pll':
      rvx_workspace.imp_fpga_pll(platform_name, args.target_imp_class, imp_instance_path)
    elif cmd_list[1]=='top':
      rvx_workspace.imp_fpga_top_module(platform_name, args.target_imp_class, imp_instance_path)
    elif cmd_list[1]=='xci':
      rvx_workspace.imp_fpga_xci(platform_name, args.target_imp_class, imp_instance_path)
    elif cmd_list[1]=='path':
      rvx_workspace.imp_fpga_path(platform_name, args.target_imp_class, imp_instance_path)
    elif cmd_list[1]=='tcl':
      rvx_workspace.imp_fpga_tcl(platform_name, args.target_imp_class, imp_instance_path)
    elif cmd_list[1]=='info':
      rvx_workspace.imp_fpga_info(imp_instance_path)

    elif cmd_list[1]=='clean':
      rvx_workspace.imp_fpga_clean(platform_name, args.target_imp_class, imp_instance_path)

    elif cmd_list[1]=='build':
      rvx_workspace.imp_fpga_build(platform_name, app_name, args.target_imp_class, args.build_mode)
    elif cmd_list[1]=='clean_build':
      rvx_workspace.imp_fpga_clean_build(platform_name, app_name, args.target_imp_class, args.build_mode, imp_instance_path)
    elif cmd_list[1]=='after_build':
      rvx_workspace.imp_fpga_after_build(platform_name, app_name, args.target_imp_class, args.build_mode, imp_instance_path)
    
    elif cmd_list[1]=='run':
      rvx_workspace.imp_fpga_run(platform_name, app_name, args.target_imp_class, args.build_mode, imp_instance_path)
    elif cmd_list[1]=='run_verify':
      rvx_workspace.imp_fpga_run_verify(platform_name, app_name, args.target_imp_class, args.build_mode, imp_instance_path)

    elif cmd_list[1]=='app_flash':
      rvx_workspace.imp_fpga_app_flash(platform_name, app_name, args.target_imp_class, args.build_mode, imp_instance_path)
    
    elif cmd_list[1]=='gen_flash_script':
      rvx_workspace.imp_fpga_gen_flash_script(platform_name, app_name, args.target_imp_class, imp_instance_path)

    elif cmd_list[1]=='__project':
      rvx_workspace.imp_fpga___project(platform_name, args.target_imp_class, imp_instance_path)
    elif cmd_list[1]=='project':
      if len(cmd_list)==2:
        rvx_workspace.imp_fpga_project(platform_name, args.target_imp_class, imp_instance_path)
      elif cmd_list[2]=='request':
        rvx_workspace.imp_fpga_project_request(platform_name, args.target_imp_class, imp_instance_path)
      elif cmd_list[2]=='check':
        rvx_workspace.imp_fpga_project_check(platform_name, imp_instance_path)
      elif cmd_list[2]=='finalize':
        rvx_workspace.imp_fpga_project_finalize(imp_instance_path)
      else:
        assert 0, cmd_list
    elif cmd_list[1]=='open_project' or cmd_list[1]=='open':
      rvx_workspace.imp_fpga_open_project(imp_instance_path)
    elif cmd_list[1]=='verify_apps':
      rvx_workspace.imp_fpga_verify_apps(platform_name, args.target_imp_class, args.build_mode, imp_instance_path)

    elif cmd_list[1]=='__imp':
      rvx_workspace.imp_fpga___imp(platform_name, args.target_imp_class, imp_instance_path)
    elif cmd_list[1]=='imp':
      if len(cmd_list)==2:
        rvx_workspace.imp_fpga_imp(platform_name, args.target_imp_class, imp_instance_path)
      elif cmd_list[2]=='request':
        rvx_workspace.imp_fpga_imp_request(imp_instance_path)
      elif cmd_list[2]=='check':
        rvx_workspace.imp_fpga_imp_check(platform_name, imp_instance_path)
      elif cmd_list[2]=='finalize':
        rvx_workspace.imp_fpga_imp_finalize(imp_instance_path)
      else:
        assert 0, cmd_list
    elif cmd_list[1]=='reimp':
      rvx_workspace.imp_fpga_reimp(platform_name, args.target_imp_class, imp_instance_path)

    elif cmd_list[1]=='check_imp' or cmd_list[1]=='check':
      rvx_workspace.imp_fpga_check_imp(imp_instance_path)

    elif cmd_list[1]=='program':
      rvx_workspace.imp_fpga_program(platform_name, args.target_imp_class, imp_instance_path)
    elif cmd_list[1]=='mcs':
      rvx_workspace.imp_fpga_mcs(imp_instance_path)
    elif cmd_list[1]=='program_flash':
      rvx_workspace.imp_fpga_program_flash(platform_name, args.target_imp_class, imp_instance_path)

    elif cmd_list[1]=='ila':
      rvx_workspace.imp_fpga_ila(platform_name, args.target_imp_class, imp_instance_path)

    elif cmd_list[1]=='ila_clean':
      rvx_workspace.imp_fpga_ila_clean(imp_instance_path)

    elif cmd_list[1]=='printf':
      rvx_workspace.imp_fpga_printf(args.target_imp_class, imp_instance_path)

    elif cmd_list[1]=='run_ocd':
      rvx_workspace.imp_fpga_run_ocd(args.target_imp_class, imp_instance_path)

    elif cmd_list[1]=='dump':
      rvx_workspace.imp_fpga_dump(args.target_imp_class, imp_instance_path)
    
    elif cmd_list[1]=='dump_flash_image':
      rvx_workspace.imp_fpga_dump_flash_image(platform_name, args.target_imp_class, imp_instance_path)

    elif cmd_list[1]=='check_dumped_image' or cmd_list[1]=='check_image':
      rvx_workspace.imp_fpga_check_dumped_image(args.target_imp_class, imp_instance_path)

    elif cmd_list[1]=='connect_ocd':
      rvx_workspace.imp_fpga_connect_ocd(imp_instance_path)

    elif cmd_list[1]=='app_list':
      rvx_workspace.print_app_list(platform_name)
      rvx_workspace.gen_app_list(platform_name, imp_instance_path)

    elif cmd_list[1]=='manual_top':
      rvx_workspace.imp_fpga_manual_top(platform_name, args.target_imp_class, imp_instance_path)    

    else:
      assert 0, cmd_list

  else:
      assert 0, cmd_list
  
  if (len(cmd_list) >=2) and cmd_list[1].endswith('clean'):
    engine_log.clean()
  else:
    engine_log.add_new_job('engine', True, 'done')
    engine_log.export_file()
