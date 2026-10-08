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

include ${RVX_RELEASE_HOME}/rvx_config_path.mh

TEMPLATE_FILE = ${RVX_DEVKIT_HOME}/makefile/Makefile.app.template
include ${RVX_UTIL_HOME}/template_makefile.mh

PLATFORM_DIR = $(abspath ${CURDIR}/../..)
PLATFORM_NAME = $(notdir ${PLATFORM_DIR})

APP_NAME = $(notdir ${CURDIR})

TARGET_IMP_CLASS ?= rtl
BUILD_MODE ?= release

ENGINE_WS=${PLATFORM_DIR}/..
ENGINE_TARGET=app
ENGINE_USER_CMD_LIST=build clean
ENGINE_USER_CMD_ADV_LIST=
ENGINE_SYSTEM_CMD_LIST=path build_dir compile_list compile compile_incremental
ENGINE_PARA= -p ${PLATFORM_NAME} -a ${APP_NAME} -tic ${TARGET_IMP_CLASS} -bm ${BUILD_MODE}
GUI_CMD_PARA_LIST=build:TARGET_IMP_CLASS
include ${RVX_DEVKIT_HOME}/engine/rvx_make2engine.mh

FPGA_LIST := $(shell ${PYTHON3_CMD} ${RVX_DEVKIT_HOME}/engine/rvx_unified_engine.py -ws ${ENGINE_WS} -cmd platform.fpga_list -p ${PLATFORM_NAME} -log ${ENGINE_LOG_DIR} 2>/dev/null)
IMP_LIST = rtl ${FPGA_LIST}

${IMP_LIST}:
	@make --no-print-directory build TARGET_IMP_CLASS=$@ BUILD_MODE=$(BUILD_MODE)

