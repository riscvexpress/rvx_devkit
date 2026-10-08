import os
import io
import argparse
import tkinter as tk
import tkinter.font as tkFont
import import_util

from pathlib import *
from os_util import *

if __name__ == '__main__':
  # parse argument
  parser = argparse.ArgumentParser(description='Converting Input Files')
  parser.add_argument('-path', '-p', help='Imp path')
  parser.add_argument('-app', '-a', nargs='+', help='App list')
  parser.add_argument('-cmd', '-c', nargs='+', help='Command list')
  parser.add_argument('-font', '-f', help='Font')
  args = parser.parse_args()

  assert args.path
  assert args.app
  assert args.cmd

  imp_path = Path(args.path).resolve().absolute()
  assert imp_path.is_dir(), imp_path
  app_name_list = args.app
  default_app_list = ['hello','flash_server']
  for default_app in default_app_list:
    if default_app in app_name_list:
      app_name_list.remove(default_app)
    else:
      default_app_list.remove(default_app)
  app_name_list = default_app_list + sorted(app_name_list)
  command_list = list(args.cmd) # DO NOT SORT
  assert len(app_name_list) > 0, app_name_list
  if args.font:
    font_size = int(args.font)
  else:
    font_size = 16
    
  is_dev_mode = 'RVX_DEV_UTIL_HOME' in os.environ
  platform_path = (imp_path / '..').absolute()
  app_base_path = platform_path / 'app'

  #
  main_window = tk.Tk()
  main_window.title('RVX Brief GUI')
  if is_dev_mode:
    main_window.title('RVX Brief GUI with Advanced Feature')
  else:
    main_window.title('RVX Brief GUI')
  font_style = tkFont.Font(family="Arial", size=font_size)
  
  row_index = 0
  col_index_for_app = 2
  column_size = (2*len(app_name_list))+col_index_for_app
  
  #
  label = tk.Label(main_window, text=imp_path, font=font_style)
  label.grid(row=row_index, column=0, columnspan=column_size, sticky="we", padx=5, pady=1)
  row_index += 1
  
  #
  hline = tk.Frame(main_window, height=2, bd=1, relief="sunken", bg="black")
  hline.grid(row=row_index, column=0, columnspan=column_size, sticky="we", padx=5, pady=1)
  row_index += 1

  #
  app_labels = []
  vline_start_index = row_index
  for i, app_name in enumerate(app_name_list):
    label = tk.Label(main_window, text=app_name, font=font_style)
    label.grid(row=row_index, column=(2*i)+col_index_for_app, padx=5, pady=1)
    app_labels.append(label)
  row_index += 1
  
  #
  hline = tk.Frame(main_window, height=2, bd=1, relief="sunken", bg="black")
  hline.grid(row=row_index, column=0, columnspan=column_size, sticky="we", padx=5, pady=1)
  row_index += 1

  # command
  dev_command_list = ('reimport_app','backup_app')
  if is_dev_mode:
    command_list += dev_command_list
  command_labels = []
  for i, command in enumerate(command_list):
    label = tk.Label(main_window, text=command, font=font_style)
    label.grid(row=row_index+i, column=0, padx=5, pady=1)
    command_labels.append(label)
  row_end_index = row_index + len(command_list)

  #
  def generate_button_command(app_index:int, command_index:int):
    def execute():
      command = command_list[command_index]
      make_target = f'{app_name_list[app_index]}.{command}'
      make_command = f'make --no-print-directory {make_target}'
      if command in dev_command_list:
        if command=='reimport_app':
          exe_path = app_base_path
        elif command=='backup_app':
          exe_path = app_base_path
        else:
          assert 0, command
      else:
        exe_path = imp_path
      print(f'\n[DIR] {exe_path}')
      print(f'[START] {make_target}')
      run_shell_cmd(cmd=make_command,cwd=exe_path, stdout=None, stderr=None, asserts_when_error=False)
      print(f'[END] {make_target}')
    return execute

  #
  highlight_bg = '#cce5ff'  # light blue shading on hover
  buttons = [[None for _ in app_name_list] for _ in command_list]

  def generate_hover_handlers(app_index:int, command_index:int):
    def on_enter(event):
      # highlight the app (column) header and command (row) header
      app_labels[app_index].configure(bg=highlight_bg)
      command_labels[command_index].configure(bg=highlight_bg)
      # shade the whole column of buttons (same app)
      for row in buttons:
        row[app_index].configure(bg=highlight_bg)
      # shade the whole row of buttons (same command)
      for btn in buttons[command_index]:
        btn.configure(bg=highlight_bg)
    def on_leave(event):
      app_labels[app_index].configure(bg=default_label_bg)
      command_labels[command_index].configure(bg=default_label_bg)
      for row in buttons:
        row[app_index].configure(bg=default_button_bg)
      for btn in buttons[command_index]:
        btn.configure(bg=default_button_bg)
    return on_enter, on_leave

  for j, command in enumerate(command_list):
    for i, app_name in enumerate(app_name_list):
      button = tk.Button(main_window, text='O', command=generate_button_command(i,j), font=font_style)
      button.grid(row=row_index+j, column=(2*i)+col_index_for_app, padx=5, pady=1)
      buttons[j][i] = button
  # capture default background colors before binding hover handlers
  default_button_bg = buttons[0][0].cget('bg')
  default_label_bg = app_labels[0].cget('bg')
  for j, command in enumerate(command_list):
    for i, app_name in enumerate(app_name_list):
      on_enter, on_leave = generate_hover_handlers(i, j)
      buttons[j][i].bind('<Enter>', on_enter)
      buttons[j][i].bind('<Leave>', on_leave)
  row_index += len(command_list)
  vline_end_index = row_index
  
  #
  for i, app_name in enumerate(app_name_list):
    vline = tk.Frame(main_window, width=2, bg="black")
    vline.grid(row=vline_start_index, column=(2*i)+col_index_for_app-1, rowspan=vline_end_index-vline_start_index, sticky="ns", pady=5)
  
  #
  hline = tk.Frame(main_window, height=2, bd=1, relief="sunken", bg="black")
  hline.grid(row=row_index, column=0, columnspan=column_size, sticky="we", padx=5, pady=1)
  row_index += 1
  
  #
  def refresh():
    cmd = 'make --no-print-directory gui.run'
    run_shell_cmd_with_terminal(cmd=cmd, cwd=imp_path)
    main_window.destroy()
  
  button = tk.Button(main_window, text='Refresh', command=refresh, font=font_style)
  button.grid(row=row_index, column=0, columnspan=column_size, sticky="we", padx=5, pady=1)
  row_index += 1

  #
  for i in range(len(app_name_list)+col_index_for_app):
    main_window.grid_columnconfigure(i, weight=1)

  main_window.mainloop()
