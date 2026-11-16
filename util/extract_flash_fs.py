import argparse
import sys
from pathlib import Path

try:
  from littlefs import LittleFS, UserContext
except ImportError:
  print('[RVX|ERROR] littlefs-python is not installed. Run "pip install littlefs-python"')
  sys.exit(1)

class ReadOnlyContext(UserContext):
  def prog(self, cfg, block, off, data):
    raise OSError('read only')

  def erase(self, cfg, block):
    raise OSError('read only')

def extract_flash_fs(image_file:Path, block_size:int, output_dir:Path):
  image = bytearray(image_file.read_bytes())
  assert len(image) % block_size == 0, (len(image), block_size)
  fs = LittleFS(context=ReadOnlyContext(buffer=image), mount=False,
                block_size=block_size, block_count=len(image)//block_size,
                read_size=1, prog_size=256, cache_size=256, lookahead_size=32, block_cycles=500)
  fs.mount()
  output_dir.mkdir(parents=True, exist_ok=True)
  for root, dir_list, file_list in fs.walk('/'):
    for name in dir_list:
      path = f'{root.rstrip("/")}/{name}'
      print(f'{"<dir>":>10}  {path}/')
      (output_dir / path.lstrip('/')).mkdir(parents=True, exist_ok=True)
    for name in file_list:
      path = f'{root.rstrip("/")}/{name}'
      with fs.open(path, 'rb') as fin:
        data = fin.read()
      print(f'{len(data):>10}  {path}')
      (output_dir / path.lstrip('/')).write_bytes(data)
  fs.unmount()

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='extract files from a flash file system image')
  parser.add_argument('-i', '--image', required=True, help='flash file system image')
  parser.add_argument('-b', '--block_size', required=True, help='block size (FLASH_SECTOR_SIZE)')
  parser.add_argument('-o', '--output', required=True, help='output directory')
  args = parser.parse_args()
  extract_flash_fs(Path(args.image), int(args.block_size, 0), Path(args.output))
