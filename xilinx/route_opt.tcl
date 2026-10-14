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

source ./set_path.tcl
source ./set_design.tcl
source ${RVX_DEVKIT_HOME}/xilinx/__set_env.tcl

if {![file exist ${IMP_RESULT_DIR}/routed.dcp]} {
	puts "\[ERROR\] ${IMP_RESULT_DIR}/routed.dcp does not exist. Please run imp first\n\n"
	exit 1
}

open_checkpoint ${IMP_RESULT_DIR}/routed.dcp
phys_opt_design -directive AggressiveExplore
write_checkpoint -force ${IMP_RESULT_DIR}/routed

source ${RVX_DEVKIT_HOME}/xilinx/__write_imp_result.tcl

close_design
