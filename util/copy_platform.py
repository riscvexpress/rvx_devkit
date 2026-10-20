import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

def rename_all(base_path:Path, before:str, after:str):
  conv_dict = {}
  for convert in (str.lower, str.upper, str.capitalize, str.title):
    conv_dict[convert(before)] = convert(after)
  re_conv = re.compile('|'.join(re.escape(x) for x in sorted(conv_dict, key=len, reverse=True)))
  replace = lambda text: re_conv.sub(lambda x: conv_dict[x.group()], text)

  path_list = sorted(base_path.rglob('*'), key=lambda x: len(x.parts), reverse=True)
  for path_object in path_list:
    if path_object.is_file() and not path_object.is_symlink():
      try:
        contents = path_object.read_bytes().decode('utf8')
      except UnicodeDecodeError:
        continue
      new_contents = replace(contents)
      if new_contents!=contents:
        path_object.write_bytes(new_contents.encode('utf8'))
  for path_object in path_list:
    new_name = replace(path_object.name)
    if new_name!=path_object.name:
      new_path = path_object.parent / new_name
      assert not new_path.exists(), new_path
      path_object.rename(new_path)

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Copy a platform')
  parser.add_argument('-input', '-i', help='source platform path')
  parser.add_argument('-output', '-o', help='target platform path')
  args = parser.parse_args()

  assert args.input
  assert args.output
  input_path = Path(args.input).absolute().resolve()
  output_path = Path(args.output).absolute().resolve()
  assert input_path.is_dir(), input_path
  assert not output_path.exists(), output_path

  input_name = input_path.name
  output_name = output_path.name
  input_xml = input_path / f'{input_name}.xml'
  assert input_xml.is_file(), input_xml

  print(f'copy {input_path} -> {output_path}', flush=True)
  removed_list = ('.log', '.rvedata', 'arch', 'fpga_component')
  re_editor_temp = re.compile(r'.*(\.sw[a-p]|\.un~|~)$')
  ignore = lambda directory, names: [x for x in names if (Path(directory)==input_path and x in removed_list) or re_editor_temp.match(x)]
  shutil.copytree(input_path, output_path, symlinks=True, ignore=ignore)
  rename_all(output_path, input_name, output_name)
  assert (output_path / f'{output_name}.xml').is_file()

  result = subprocess.run(['make', '--no-print-directory', 'clean'], cwd=output_path)
  sys.exit(result.returncode)
