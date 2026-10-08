import argparse
import shutil
import subprocess
import sys
from pathlib import Path

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
  shutil.copytree(input_path, output_path, symlinks=True)

  output_xml = output_path / f'{output_name}.xml'
  (output_path / input_xml.name).rename(output_xml)
  contents = output_xml.read_text(encoding='utf8')
  output_xml.write_text(contents.replace(f'<name>{input_name}</name>', f'<name>{output_name}</name>', 1), encoding='utf8')

  result = subprocess.run(['make', '--no-print-directory', 'clean'], cwd=output_path)
  sys.exit(result.returncode)
