import argparse
import json
from pathlib import *

from npx_cfg_parser import strip_jsonc, format_json

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Extracting the preprocess section from an NPX app file')
  parser.add_argument('-input', '-i', help='app file (<app>.snn.jsonc)')
  parser.add_argument('-output', '-o', help='preprocess file (<app>.preprocess.jsonc)')
  args = parser.parse_args()

  assert args.input
  assert args.output
  input_path = Path(args.input)
  assert input_path.is_file(), input_path

  root = json.loads(strip_jsonc(input_path.read_text()))
  assert 'preprocess' in root, f'no preprocess in {input_path}'
  Path(args.output).write_text(format_json({'preprocess': root['preprocess']}) + '\n')
