source ./set_path.tcl

source ${RVX_DEVKIT_HOME}/ocd/ervp_jtag_memorymap_offset.tcl
source ${RVX_DEVKIT_HOME}/ocd/ervp_platform_controller_memorymap_offset.tcl
source ${RVX_DEVKIT_HOME}/ocd/ervp_external_peri_group_memorymap_offset.tcl
source ${RVX_DEVKIT_HOME}/ocd/munoc_memorymap_offset.tcl

source ${PLATFORM_DIR}/arch/tcl/memorymap_info.tcl
source ${PLATFORM_DIR}/arch/tcl/hw_info.tcl
source ${PLATFORM_DIR}/arch/tcl/ssw_info.tcl

source ${RVX_DEVKIT_HOME}/ocd/util.tcl
source ${RVX_DEVKIT_HOME}/ocd/jtag_function.tcl
source ${RVX_DEVKIT_HOME}/ocd/memory_function.tcl
source ${RVX_DEVKIT_HOME}/ocd/control_function.tcl
source ${RVX_DEVKIT_HOME}/ocd/mmio_function.tcl
source ${RVX_DEVKIT_HOME}/ocd/misc_api.tcl
source ${RVX_DEVKIT_HOME}/ocd/platform_controller_api.tcl
source ${RVX_DEVKIT_HOME}/ocd/flash_api.tcl
source ${RVX_DEVKIT_HOME}/ocd/noc_api.tcl
source ${RVX_DEVKIT_HOME}/ocd/dump_api.tcl

if [info exists INCLUDE_SDRAM]==1 {
  set set_sdram_config_path ./set_sdram_config.tcl
  if [file exists $set_sdram_config_path]==1 {
    source $set_sdram_config_path
  }
}
print_platform_info
