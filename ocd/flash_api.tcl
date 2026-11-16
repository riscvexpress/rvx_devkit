# this script works only when 'program_flash' is running on a core

proc send_flash_cmd {cmd} {
	global OCD_FLASH_CMD_IDLE
	for {set i 0} {$i<10000} {incr i} {
		if {[get_gpr 0]==$OCD_FLASH_CMD_IDLE} {
			set_gpr 0 $cmd
			return
		}
	}
	error "<OCD:ERROR> flash server is not ready"
}

proc check_flash_server {} {
	global OCD_FLASH_CMD_CHECK
	global FLASH_BUFFER_ADDR
	global FLASH_BUFFER_SIZE
	send_flash_cmd $OCD_FLASH_CMD_CHECK
	wait_flash_behavior
	set FLASH_BUFFER_ADDR [get_gpr 6]
	set FLASH_BUFFER_SIZE [get_gpr 7]
}

proc wait_flash_behavior {} {
	global OCD_FLASH_CMD_IDLE
	while 1 {
		set finish [get_gpr 0]
		if {$finish==$OCD_FLASH_CMD_IDLE} {
			break
		}
	}
	set ret [get_gpr 5]
	if {[expr $ret & 0x80000000]!=0} {
		error [format "<OCD:ERROR> flash server returned error 0x%x" $ret]
	}
	return $ret
}

proc spi_flash_erase_sector {addr} {
	global OCD_FLASH_CMD_ERASE

	set_gpr 1 $addr
	send_flash_cmd $OCD_FLASH_CMD_ERASE
	wait_flash_behavior
}

proc spi_flash_program {addr num data_array} {
	global FLASH_BUFFER_ADDR
	global OCD_FLASH_CMD_WRITE
	global OCD_FLASH_CMD_IDLE
	upvar $data_array temp_array

	set_gpr 1 $addr
	set_gpr 2 [expr $num << 2]
	write_memory $FLASH_BUFFER_ADDR $num temp_array
	send_flash_cmd $OCD_FLASH_CMD_WRITE
	wait_flash_behavior
}

proc spi_flash_read {addr num data_array} {
	global FLASH_BUFFER_ADDR
	global OCD_FLASH_CMD_READ
	upvar $data_array temp_array

	set_gpr 1 $addr
	set_gpr 2 [expr $num << 2]
	send_flash_cmd $OCD_FLASH_CMD_READ
	wait_flash_behavior
	read_memory $FLASH_BUFFER_ADDR $num temp_array
}

set FLASH_DATA_INDIVIDUAL 0
set FLASH_DATA_ALL_ZERO 1
set FLASH_DATA_ALL_ONE 2
set FLASH_DATA_NA 3

proc dump_flash_fs_raw {data_file map_file temp_file offset size} {
	global FLASH_BUFFER_ADDR
	global FLASH_BUFFER_SIZE
	global OCD_FLASH_CMD_READ
	global FLASH_DATA_INDIVIDUAL
	global FLASH_FS_BASEADDR
	global FLASH_FS_SIZE

	if [info exists FLASH_FS_BASEADDR]!=1 {
		echo "<OCD:ERROR> this board has no flash file system"
		break
	}
	if {$size==0} {
		set size [expr $FLASH_FS_SIZE - $offset]
	}
	if {$offset < 0 || $size <= 0 || [expr $offset + $size] > $FLASH_FS_SIZE || [expr $offset % 4]!=0 || [expr $size % 4]!=0} {
		echo [format "<OCD:ERROR> invalid range offset 0x%x size 0x%x (fs size 0x%x)" $offset $size $FLASH_FS_SIZE]
		break
	}

	check_flash_server
	set chunk_size $FLASH_BUFFER_SIZE
	set flash_addr [expr $FLASH_FS_BASEADDR + $offset]
	set remain $size
	set buffer_addr $FLASH_BUFFER_ADDR
	set fout [open $data_file w]
	set fmap [open $map_file w]
	echo [format "<OCD:INFO> dump flash 0x%x-0x%x" $flash_addr [expr $flash_addr + $size]]
	while {$remain > 0} {
		set num_bytes $chunk_size
		if {$num_bytes > $remain} {
			set num_bytes $remain
		}
		set_gpr 1 $flash_addr
		set_gpr 2 $num_bytes
		send_flash_cmd $OCD_FLASH_CMD_READ
		wait_flash_behavior
		set pattern [get_gpr 4]
		puts $fmap [format "0x%x 0x%x %d" [expr $flash_addr - $FLASH_FS_BASEADDR] $num_bytes $pattern]
		if {$pattern==$FLASH_DATA_INDIVIDUAL} {
			dump_image $temp_file $buffer_addr $num_bytes
			set fin [open $temp_file r]
			puts -nonewline $fout [read $fin]
			close $fin
		}
		set flash_addr [expr $flash_addr + $num_bytes]
		set remain [expr $remain - $num_bytes]
		if {[expr ($size - $remain) % 0x100000]==0} {
			echo [format "<OCD:INFO> %d / %d KB" [expr ($size - $remain) >> 10] [expr $size >> 10]]
		}
	}
	close $fout
	close $fmap
	if [file exists $temp_file]==1 {
		file delete $temp_file
	}
	echo [format "<OCD:INFO> dumped %d bytes" $size]
}

proc dump_flash_fs {data_file map_file temp_file} {
	global FLASH_BUFFER_ADDR
	global FLASH_BUFFER_SIZE
	global OCD_FLASH_CMD_FS_READ_BLOCK
	global FLASH_DATA_INDIVIDUAL
	global FLASH_DATA_NA
	global FLASH_FS_BASEADDR

	if [info exists FLASH_FS_BASEADDR]!=1 {
		error "<OCD:ERROR> this board has no flash file system"
	}

	check_flash_server
	set fout [open $data_file w]
	set fmap [open $map_file w]
	set num_chunks 0
	while 1 {
		send_flash_cmd $OCD_FLASH_CMD_FS_READ_BLOCK
		set offset [wait_flash_behavior]
		set pattern [get_gpr 4]
		if {$pattern==$FLASH_DATA_NA} {
			break
		}
		puts $fmap [format "0x%x 0x%x %d" $offset $FLASH_BUFFER_SIZE $pattern]
		if {$pattern==$FLASH_DATA_INDIVIDUAL} {
			dump_image $temp_file $FLASH_BUFFER_ADDR $FLASH_BUFFER_SIZE
			set fin [open $temp_file r]
			puts -nonewline $fout [read $fin]
			close $fin
		}
		incr num_chunks
		if {[expr $num_chunks % 128]==0} {
			echo [format "<OCD:INFO> %d KB" [expr ($num_chunks * $FLASH_BUFFER_SIZE) >> 10]]
		}
	}
	close $fout
	close $fmap
	if [file exists $temp_file]==1 {
		file delete $temp_file
	}
	echo [format "<OCD:INFO> dumped %d bytes in used blocks" [expr $num_chunks * $FLASH_BUFFER_SIZE]]
}

proc load_flash_buffer {temp_file data} {
	global FLASH_BUFFER_ADDR
	set num_pad [expr (4 - ([string bytelength $data] & 3)) & 3]
	set ftemp [open $temp_file wb]
	puts -nonewline $ftemp $data
	puts -nonewline $ftemp [string repeat "\x00" $num_pad]
	close $ftemp
	load_image $temp_file $FLASH_BUFFER_ADDR bin
}

proc write_flash_fs_file {local_file fs_path temp_file} {
	global FLASH_BUFFER_SIZE
	global OCD_FLASH_CMD_FS_FILE_OPEN
	global OCD_FLASH_CMD_FS_FILE_WRITE
	global OCD_FLASH_CMD_FS_FILE_CLOSE
	global FLASH_FS_BASEADDR

	if [info exists FLASH_FS_BASEADDR]!=1 {
		error "<OCD:ERROR> this board has no flash file system"
	}

	check_flash_server
	set file_size [file size $local_file]
	load_flash_buffer $temp_file "$fs_path\x00"
	set_gpr 2 $file_size
	send_flash_cmd $OCD_FLASH_CMD_FS_FILE_OPEN
	wait_flash_behavior

	set fin [open $local_file rb]
	set written 0
	set num_chunks 0
	while {$written < $file_size} {
		set num_bytes [expr $file_size - $written]
		if {$num_bytes > $FLASH_BUFFER_SIZE} {
			set num_bytes $FLASH_BUFFER_SIZE
		}
		load_flash_buffer $temp_file [read $fin $num_bytes]
		set_gpr 2 $num_bytes
		send_flash_cmd $OCD_FLASH_CMD_FS_FILE_WRITE
		wait_flash_behavior
		set written [expr $written + $num_bytes]
		incr num_chunks
		if {[expr $num_chunks % 128]==0} {
			echo [format "<OCD:INFO> %d / %d KB" [expr $written >> 10] [expr $file_size >> 10]]
		}
	}
	close $fin

	send_flash_cmd $OCD_FLASH_CMD_FS_FILE_CLOSE
	set size [wait_flash_behavior]
	if [file exists $temp_file]==1 {
		file delete $temp_file
	}
	if {$size!=$file_size} {
		error [format "<OCD:ERROR> %s is %d bytes, but %d bytes are written" $fs_path $file_size $size]
	}
	echo [format "<OCD:INFO> wrote %s %d bytes" $fs_path $size]
}

proc print_flash_data {addr num} {
	spi_flash_read $addr $num data_array
	for {set i 0} {$i<$num} {set i [expr $i + 1]} {
		set data_array($i) [dec2hex $data_array($i)]
	}
	parray data_array
}

proc program_app_to_flash {addr app_name} {
	global FLASH_BUFFER_ADDR
  global APP_ADDR
	global SMALL_RAM_BASEADDR
	global LARGE_RAM_BASEADDR
	global OCD_FLASH_CMD_WRITE
  global INCLUDE_SDRAM
  global I_SYSTEM_SDRAM_CTRL_BASEADDR
	global HAS_NO_FLASH
	global FLASH_SECTOR_SIZE
	global FLASH_BINARY_BASEADDR
	global FLASH_BINARY_SIZE
	global FLASH_FS_BASEADDR
	global FLASH_FS_SIZE

	if [info exists HAS_NO_FLASH]==1 {
		echo "<OCD:ERROR> this board has no flash for applications"
		break
	}

	set buffer_size 0x1000
	set sector_size 0x10000
	if [info exists FLASH_SECTOR_SIZE]==1 {
		set sector_size $FLASH_SECTOR_SIZE
	}

	set sram_hex_path ./${app_name}.sram.hex
	if [file exists $sram_hex_path]!=1 {
		echo [format "<OCD:ERROR> no hex file \"%s\"" $sram_hex_path]
		break
	}
	set sram_hex_size [get_hex_file_size $sram_hex_path]
	set sram_contents_size [expr $sram_hex_size + 2]

	set dram_hex_path ./${app_name}.dram.hex
	if [info exists LARGE_RAM_BASEADDR]==1 {
		if [file exists $dram_hex_path]!=1 {
			echo [format "<OCD:ERROR> no hex file \"%s\"" $dram_hex_path]
			break
		} else {
			set dram_hex_size [get_hex_file_size $dram_hex_path]
		}
	} else {
		set dram_hex_size 0
	}
	if {$dram_hex_size==0} {
		set dram_contents_size 0
	} else {
		set dram_contents_size [expr $dram_hex_size + 2]
	}
	
	set total_contents_size [expr $sram_contents_size + $dram_contents_size + 1]	
	set image_header_size 68
	if [info exists FLASH_FS_BASEADDR]==1 {
		set image_header_size [expr $image_header_size + 32]
	}
	set image_end [expr $addr + $total_contents_size + $image_header_size]
	set first_sector_addr [expr $addr - [expr $addr % $sector_size]]
	set num_sector [expr [expr [expr $image_end - 1 - $first_sector_addr] / $sector_size] + 1]

	set binary_base 0
	set binary_end 0x1000000
	if [info exists FLASH_BINARY_SIZE]==1 {
		set binary_base $FLASH_BINARY_BASEADDR
		set binary_end [expr $FLASH_BINARY_BASEADDR + $FLASH_BINARY_SIZE]
	}
	if {$addr < $binary_base || $image_end > $binary_end} {
		echo [format "<OCD:ERROR> app image 0x%x-0x%x is outside flash binary region 0x%x-0x%x" $addr $image_end $binary_base $binary_end]
		break
	}

	# erase sectors
	check_flash_server
	for {set i 0} {$i<$num_sector} {set i [expr $i + 1]} {
		set sector_addr [expr $first_sector_addr + [expr $sector_size * $i]]
		spi_flash_erase_sector $sector_addr
	}

	# prepare
	set flash_addr $addr
	set buffered_bytes 0
	set memory_addr $FLASH_BUFFER_ADDR

  # write sdram config
  if [info exists INCLUDE_SDRAM]==1 {
    # size
    write_single $memory_addr 12
    set buffered_bytes [expr $buffered_bytes + 4]
    set memory_addr [expr $memory_addr + 4]
    # addr
    write_single $memory_addr $I_SYSTEM_SDRAM_CTRL_BASEADDR
    set buffered_bytes [expr $buffered_bytes + 4]
    set memory_addr [expr $memory_addr + 4]
    # wunit
    write_single $memory_addr 4
    set buffered_bytes [expr $buffered_bytes + 4]
    set memory_addr [expr $memory_addr + 4]
    # data 0
    set config [read_single [expr $I_SYSTEM_SDRAM_CTRL_BASEADDR + 0]]
    write_single $memory_addr $config
    set buffered_bytes [expr $buffered_bytes + 4]
    set memory_addr [expr $memory_addr + 4]
    # data 4
    set config [read_single [expr $I_SYSTEM_SDRAM_CTRL_BASEADDR + 4]]
    write_single $memory_addr $config
    set buffered_bytes [expr $buffered_bytes + 4]
    set memory_addr [expr $memory_addr + 4]
    # data 8
    set config [read_single [expr $I_SYSTEM_SDRAM_CTRL_BASEADDR + 8]]
    write_single $memory_addr $config
    set buffered_bytes [expr $buffered_bytes + 4]
    set memory_addr [expr $memory_addr + 4]
    print_sdram_config
  }

  ## write app_addr
  # size
  write_single $memory_addr 4
  set buffered_bytes [expr $buffered_bytes + 4]
  set memory_addr [expr $memory_addr + 4]
  # addr
  write_single $memory_addr [get_app_addr_addr]
  set buffered_bytes [expr $buffered_bytes + 4]
  set memory_addr [expr $memory_addr + 4]
  # wunit
  write_single $memory_addr 4
  set buffered_bytes [expr $buffered_bytes + 4]
  set memory_addr [expr $memory_addr + 4]
  # data
  write_single $memory_addr $APP_ADDR
  set buffered_bytes [expr $buffered_bytes + 4]
  set memory_addr [expr $memory_addr + 4]

  ## write flash_fs_baseaddr, flash_fs_size
  if [info exists FLASH_FS_BASEADDR]==1 {
    # size
    write_single $memory_addr 4
    set buffered_bytes [expr $buffered_bytes + 4]
    set memory_addr [expr $memory_addr + 4]
    # addr
    write_single $memory_addr [get_flash_fs_baseaddr_addr]
    set buffered_bytes [expr $buffered_bytes + 4]
    set memory_addr [expr $memory_addr + 4]
    # wunit
    write_single $memory_addr 4
    set buffered_bytes [expr $buffered_bytes + 4]
    set memory_addr [expr $memory_addr + 4]
    # data
    write_single $memory_addr $FLASH_FS_BASEADDR
    set buffered_bytes [expr $buffered_bytes + 4]
    set memory_addr [expr $memory_addr + 4]
    # size
    write_single $memory_addr 4
    set buffered_bytes [expr $buffered_bytes + 4]
    set memory_addr [expr $memory_addr + 4]
    # addr
    write_single $memory_addr [get_flash_fs_size_addr]
    set buffered_bytes [expr $buffered_bytes + 4]
    set memory_addr [expr $memory_addr + 4]
    # wunit
    write_single $memory_addr 4
    set buffered_bytes [expr $buffered_bytes + 4]
    set memory_addr [expr $memory_addr + 4]
    # data
    write_single $memory_addr $FLASH_FS_SIZE
    set buffered_bytes [expr $buffered_bytes + 4]
    set memory_addr [expr $memory_addr + 4]
  }

	## write sram contents ##
	set hex_path $sram_hex_path
	set hex_size $sram_hex_size
	if {$hex_size==0} {
		set target_addr $SMALL_RAM_BASEADDR
	} else {
		set target_addr $SMALL_RAM_BASEADDR
	}

	if {$hex_size > 0} {
		# read file
		set f [open $hex_path r]
		echo [format "\n<OCD:INFO> hex to flash \"%s\" %d bytes" $hex_path $hex_size]

		# write size to memory
		write_single $memory_addr $hex_size
		set buffered_bytes [expr $buffered_bytes + 4]
		set memory_addr [expr $memory_addr + 4]

		if {$buffered_bytes==$buffer_size} {
			set_gpr 1 $flash_addr
			set_gpr 2 $buffered_bytes
			send_flash_cmd $OCD_FLASH_CMD_WRITE
			wait_flash_behavior
			set flash_addr [expr $flash_addr + $buffered_bytes]
			set buffered_bytes 0
			set memory_addr $FLASH_BUFFER_ADDR
		}

		# write addr to memory
		write_single $memory_addr $target_addr
		set buffered_bytes [expr $buffered_bytes + 4]
		set memory_addr [expr $memory_addr + 4]

		if {$buffered_bytes==$buffer_size} {
			set_gpr 1 $flash_addr
			set_gpr 2 $buffered_bytes
			send_flash_cmd $OCD_FLASH_CMD_WRITE
			wait_flash_behavior
			set flash_addr [expr $flash_addr + $buffered_bytes]
			set buffered_bytes 0
			set memory_addr $FLASH_BUFFER_ADDR
		}

    # write wunit to memory
		write_single $memory_addr 1
		set buffered_bytes [expr $buffered_bytes + 4]
		set memory_addr [expr $memory_addr + 4]

		if {$buffered_bytes==$buffer_size} {
			set_gpr 1 $flash_addr
			set_gpr 2 $buffered_bytes
			send_flash_cmd $OCD_FLASH_CMD_WRITE
			wait_flash_behavior
			set flash_addr [expr $flash_addr + $buffered_bytes]
			set buffered_bytes 0
			set memory_addr $FLASH_BUFFER_ADDR
		}

		# write hex to memory
		while {[eof $f]==0} {
			set data {}
			for {set i 0} {$i<8} {set i [expr $i + 2]} {
				set buffer [read $f 2]
				set data [append buffer $data]
			}
			if {[string length $data]!=0} {
				set buffer "0x"
				set data [append buffer $data]
				#echo [format "addr: %x data: %x" $memory_addr $data]
				write_single $memory_addr $data
			}
			set buffered_bytes [expr $buffered_bytes + 4]
			set memory_addr [expr $memory_addr + 4]
			# read \n
			read $f 1

			if {$buffered_bytes==$buffer_size} {
				# program flash
				set_gpr 1 $flash_addr
				set_gpr 2 $buffered_bytes
				send_flash_cmd $OCD_FLASH_CMD_WRITE
				wait_flash_behavior
				set flash_addr [expr $flash_addr + $buffered_bytes]
				set buffered_bytes 0
				set memory_addr $FLASH_BUFFER_ADDR
			}
		}
	}

	## write dram contents ##
	set hex_path $dram_hex_path
	set hex_size $dram_hex_size
	if {$hex_size==0} {
		set target_addr $SMALL_RAM_BASEADDR
	} else {
		set target_addr $LARGE_RAM_BASEADDR
	}

	if {$hex_size > 0} {
		# read file
		set f [open $hex_path r]
		echo [format "\n<OCD:INFO> hex to flash \"%s\" %d bytes" $hex_path $hex_size]

		# write size to memory
		write_single $memory_addr $hex_size
		set buffered_bytes [expr $buffered_bytes + 4]
		set memory_addr [expr $memory_addr + 4]

		if {$buffered_bytes==$buffer_size} {
			set_gpr 1 $flash_addr
			set_gpr 2 $buffered_bytes
			send_flash_cmd $OCD_FLASH_CMD_WRITE
			wait_flash_behavior
			set flash_addr [expr $flash_addr + $buffered_bytes]
			set buffered_bytes 0
			set memory_addr $FLASH_BUFFER_ADDR
		}

		# write addr to memory
		write_single $memory_addr $target_addr
		set buffered_bytes [expr $buffered_bytes + 4]
		set memory_addr [expr $memory_addr + 4]

		if {$buffered_bytes==$buffer_size} {
			set_gpr 1 $flash_addr
			set_gpr 2 $buffered_bytes
			send_flash_cmd $OCD_FLASH_CMD_WRITE
			wait_flash_behavior
			set flash_addr [expr $flash_addr + $buffered_bytes]
			set buffered_bytes 0
			set memory_addr $FLASH_BUFFER_ADDR
		}

    # write wunit to memory
		write_single $memory_addr 1
		set buffered_bytes [expr $buffered_bytes + 4]
		set memory_addr [expr $memory_addr + 4]

		if {$buffered_bytes==$buffer_size} {
			set_gpr 1 $flash_addr
			set_gpr 2 $buffered_bytes
			send_flash_cmd $OCD_FLASH_CMD_WRITE
			wait_flash_behavior
			set flash_addr [expr $flash_addr + $buffered_bytes]
			set buffered_bytes 0
			set memory_addr $FLASH_BUFFER_ADDR
		}

		# write hex to memory
		while {[eof $f]==0} {
			set data {}
			for {set i 0} {$i<8} {set i [expr $i + 2]} {
				set buffer [read $f 2]
				set data [append buffer $data]
			}
			if {[string length $data]!=0} {
				set buffer "0x"
				set data [append buffer $data]
				#echo [format "addr: %x data: %x" $memory_addr $data]
				write_single $memory_addr $data
			}
			set buffered_bytes [expr $buffered_bytes + 4]
			set memory_addr [expr $memory_addr + 4]
			# read \n
			read $f 1

			if {$buffered_bytes==$buffer_size} {
				# program flash
				set_gpr 1 $flash_addr
				set_gpr 2 $buffered_bytes
				send_flash_cmd $OCD_FLASH_CMD_WRITE
				wait_flash_behavior
				set flash_addr [expr $flash_addr + $buffered_bytes]
				set buffered_bytes 0
				set memory_addr $FLASH_BUFFER_ADDR
			}
		}
	}

	## write zero to memory ##
	write_single $memory_addr 0
	set buffered_bytes [expr $buffered_bytes + 4]
	set memory_addr [expr $memory_addr + 4]

	## write back the remains ##
	if {$buffered_bytes>0} {
		set_gpr 1 $flash_addr
		set_gpr 2 $buffered_bytes
		send_flash_cmd $OCD_FLASH_CMD_WRITE
		wait_flash_behavior
	}
}

proc test_flash {} {
	global FLASH_BUFFER_ADDR
	set a(0) 4
	set a(1) 1
	set a(2) 7
	set a(3) 9
	set a(4) 9
	set a(5) 3
	set a(6) 2
	set a(7) 8

	set size 8

	check_flash_server
	set flash_addr [get_flash_binary_baseaddr]
	spi_flash_erase_sector $flash_addr
	spi_flash_program $flash_addr $size a
	mww $FLASH_BUFFER_ADDR 0 $size
	print_flash_data $flash_addr $size
}

proc test_hex_to_flash {} {
	set flash_addr [get_flash_binary_baseaddr]
	program_app_to_flash $flash_addr hello
	print_flash_data $flash_addr 8
}

proc program_flash {app_name} {
	global PLATFORM_NAME
	global SMALL_RAM_BASEADDR
	global BOOT_MODE_OCD
	
	echo [format "<OCD:INFO> app \'%s\' will be programmed to flash" $app_name]
	set flash_addr [get_flash_binary_baseaddr]
	program_app_to_flash $flash_addr $app_name
	print_flash_data $flash_addr 8

	echo [format "<OCD:INFO> programmed successfully"]
}
