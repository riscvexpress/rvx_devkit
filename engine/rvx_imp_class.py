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

import xml.etree.ElementTree as ET
import argparse
import os

from pathlib import Path

class RvxImpClass():
  def __init__(self):
    self.clear()

  def clear(self):
    self.imp_class_dict = {}
    self.file_dict = {}
    self.fpga_list = []
    self.unique_instance_list = []

  def import_xml(self, xml_path:Path): 
    assert xml_path.is_file(), xml_path
    xml_tree = ET.parse(str(xml_path))
    xml_root = xml_tree.getroot()
    assert xml_root.tag=='rvx', xml_root.tag
    assert len(xml_root)==1, len(xml_root)
    assert xml_root[0].tag=='imp_class_list', xml_root[0].tag
    for imp_class_xml in xml_root[0].findall('imp_class'):
      imp_class_info = RvxImpClass.xml2dict(imp_class_xml)
      name = imp_class_info['name']
      type = imp_class_info['type']
      is_new = name not in self.imp_class_dict
      if not is_new:
        if name in self.fpga_list:
          self.fpga_list.remove(name)
        self.unique_instance_list = [x for x in self.unique_instance_list if x[1]!=name]
      self.imp_class_dict[name] = imp_class_info
      self.file_dict[name] = xml_path
      if type=='fpga':
        self.fpga_list.append(name)
      unique_instance = imp_class_info.get('unique_instance')
      if unique_instance:
        assert name==type
        self.unique_instance_list.append((unique_instance,type,type))

  @staticmethod
  def xml2dict(xml_element):
    if len(xml_element):
      result = {}
      for xml_child in xml_element:
        result[xml_child.tag] = RvxImpClass.xml2dict(xml_child)
    else:
      result = xml_element.text
    return result

  def get_imp_class_info(self, imp_name:str):
    return self.imp_class_dict.get(imp_name)

  @property
  def imp_class_list(self):
    return self.imp_class_dict.keys()

  def get_fpga_info(self, fpga_name:str):
    result = None
    if fpga_name in self.fpga_list:
      result = self.get_imp_class_info(fpga_name)
      if result:
        result = result.get('fpga_info')
    return result

  def get_flash_var_dict(self, imp_name:str):
    result = {}
    imp_class_info = self.get_imp_class_info(imp_name)
    flash = imp_class_info.get('flash') if imp_class_info else None
    if not flash:
      result['HAS_NO_FLASH'] = None
    else:
      is_unified = 'unified_flash' in flash
      is_separate = 'separate_flash' in flash
      assert is_unified != is_separate, imp_name
      result['HAS_FLASH'] = None
      result['FLASH_DEVICE'] = flash['device']
      if is_unified:
        result['FLASH_IS_UNIFIED'] = None
      else:
        result['FLASH_IS_SEPARATE'] = None
      if 'qspi' in flash:
        result['FLASH_IS_QSPI'] = None
      result['FLASH_SIZE'] = flash['size']
      result['FLASH_SECTOR_SIZE'] = flash['sector_size']
      if 'spi_freq_hz' in flash:
        result['FLASH_SPI_FREQ_HZ'] = flash['spi_freq_hz']
      layout = flash.get('flash_layout', {})
      for tag, name in (('bitstream_base_addr', 'FLASH_BITSTREAM_BASEADDR'),
                        ('bitstream_size', 'FLASH_BITSTREAM_SIZE'),
                        ('binary_base_addr', 'FLASH_BINARY_BASEADDR'),
                        ('binary_size', 'FLASH_BINARY_SIZE'),
                        ('fs_base_addr', 'FLASH_FS_BASEADDR'),
                        ('fs_size', 'FLASH_FS_SIZE')):
        if tag in layout:
          result[name] = layout[tag]
    return result

  def generate_flash_info_tcl(self, imp_name:str):
    line_list = []
    for name, value in self.get_flash_var_dict(imp_name).items():
      if name=='FLASH_DEVICE':
        value = f'"{value}"'
      line_list.append(f'set {name} {1 if value is None else value}')
    return '\n'.join(line_list) + '\n'

  def generate_flash_info_header(self, imp_name:str):
    line_list = ['#ifndef __FLASH_INFO_H__', '#define __FLASH_INFO_H__', '']
    for name, value in self.get_flash_var_dict(imp_name).items():
      if name=='FLASH_DEVICE':
        value = f'"{value}"'
      line_list.append(f'#define {name}' if value is None else f'#define {name} {value}')
    line_list += ['', '#endif']
    return '\n'.join(line_list) + '\n'

  def generate_flash_info_vh(self, imp_name:str):
    line_list = ['`ifndef __FLASH_INFO_VH__', '`define __FLASH_INFO_VH__', '']
    flash_var_dict = self.get_flash_var_dict(imp_name)
    for name in ('FLASH_FS_BASEADDR', 'FLASH_FS_SIZE'):
      if name in flash_var_dict:
        line_list.append(f"`define {name} 32'h{int(flash_var_dict[name], 0):x}")
    line_list += ['', '`endif']
    return '\n'.join(line_list) + '\n'
