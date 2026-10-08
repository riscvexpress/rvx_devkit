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

TEMPLATE_FILE = ${RVX_DEVKIT_HOME}/makefile/Makefile.app_base.template
include ${RVX_UTIL_HOME}/template_makefile.mh

PLATFORM_DIR = $(abspath ${CURDIR}/..)
PLATFORM_NAME = $(notdir ${PLATFORM_DIR})
RVX_WORKSPACE = $(abspath ${PLATFORM_DIR}/..)

APP_NAME ?= Base

ENGINE_WS=${PLATFORM_DIR}/..
ENGINE_TARGET=app
ENGINE_USER_CMD_LIST=new delete clean
ENGINE_USER_CMD_ADV_LIST= 
ENGINE_PARA= -p ${PLATFORM_NAME} -a ${APP_NAME}
GUI_CMD_PARA_LIST=new:APP_NAME delete:APP_NAME
include ${RVX_DEVKIT_HOME}/engine/rvx_make2engine.mh

APP_BASE_DIR=${CURDIR}
-include ${RVX_DEV_UTIL_HOME}/makefile_template/rvx_dev_util.mh
