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
## 2019-04 : Kyuseung Han (han@etri.re.kr)
## ****************************************************************************
## ****************************************************************************

report_route_status -file ${IMP_RESULT_DIR}/route_status.rpt
report_timing_summary -file ${IMP_RESULT_DIR}/route_timing_summary.rpt
report_timing -sort_by group -max_paths 100 -path_type summary -file ${IMP_RESULT_DIR}/route_timing_max.rpt
report_clock_utilization -file ${IMP_RESULT_DIR}/clock_util.rpt
report_utilization -file ${IMP_RESULT_DIR}/route_util.rpt
report_utilization -hierarchical  -file ${IMP_RESULT_DIR}/route_util_hier.rpt
report_power -file ${IMP_RESULT_DIR}/route_power.rpt
report_power -hier all -hierarchical_depth 10 -file ${IMP_RESULT_DIR}/route_power_hier.rpt
report_io -file ${IMP_RESULT_DIR}/route_io.rpt 
report_cdc -file ${IMP_RESULT_DIR}/route_cdc.rpt
report_cdc -details -file ${IMP_RESULT_DIR}/route_cdc_details.rpt
write_verilog -force ${IMP_RESULT_DIR}/${TOP_MODULE}.v

###############
## bitstream ##
###############

write_bitstream -force ${IMP_RESULT_DIR}/${BIT_FILE_NAME}.bit
#write_device_image -force -file ${IMP_RESULT_DIR}/${BIT_FILE_NAME}.pdi
if [string equal $IMP_MODE "debug"] {
	write_debug_probes -force ${IMP_RESULT_DIR}/${BIT_FILE_NAME}.ltx
}

touch ${IMP_RESULT_DIR}/gen_bit
