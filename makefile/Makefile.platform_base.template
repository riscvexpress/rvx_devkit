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

TEMPLATE_FILE = ${RVX_DEVKIT_HOME}/makefile/Makefile.platform_base.template
include ${RVX_UTIL_HOME}/template_makefile.mh

-include ./each_platform_base.mh

PLATFORM_NAME=Base

ENGINE_WS=${CURDIR}
ENGINE_TARGET=platform
ENGINE_USER_CMD_LIST=new delete clean
ENGINE_USER_CMD_ADV_LIST=
ENGINE_SYSTEM_CMD_LIST=import
ENGINE_PARA= -p ${PLATFORM_NAME}
MAKEFILE_USER_CMD_LIST=
MAKEFILE_USER_CMD_ADV_LIST=copy_platform
GUI_CMD_PARA_LIST=new:PLATFORM_NAME delete:PLATFORM_NAME copy_platform:BEFORE copy_platform:AFTER
include ${RVX_DEVKIT_HOME}/engine/rvx_make2engine.mh

PLATFORM_BASE_DIR=${CURDIR}

copy_platform:
	$(if ${BEFORE},,$(error define BEFORE))
	$(if ${AFTER},,$(error define AFTER))
	@${PYTHON3_CMD} ${RVX_DEVKIT_HOME}/util/copy_platform.py -i ${CURDIR}/${BEFORE} -o ${CURDIR}/${AFTER}

.PHONY: copy_platform
