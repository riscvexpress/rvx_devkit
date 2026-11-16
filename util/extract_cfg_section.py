import argparse
from pathlib import *

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Extracting a Section from a Config File')
  parser.add_argument('-input', '-i', help='input cfg file')
  parser.add_argument('-output', '-o', help='output cfg file')
  parser.add_argument('-section', '-s', default='preprocess', help='section name')
  args = parser.parse_args()

  assert args.input
  assert args.output
  input_path = Path(args.input)
  assert input_path.is_file(), input_path

  header = f'[{args.section}]'
  line_list = []
  in_section = False
  for line in input_path.read_text().splitlines():
    stripped = line.strip()
    if stripped.startswith('['):
      in_section = (stripped==header)
    if in_section:
      line_list.append(line)
  while line_list and not line_list[-1].strip():
    line_list.pop()
  assert line_list, f'no {header} in {input_path}'

  Path(args.output).write_text('\n'.join(line_list) + '\n')
