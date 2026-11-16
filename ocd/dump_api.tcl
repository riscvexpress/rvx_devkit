proc dump_memory_using_gpr {type_file data_file} {
  set type [get_gpr 5]
	set addr [get_gpr 6]
	set size [get_gpr 7]
  set fp [open $type_file w]
  puts $fp $type
  close $fp
	dump_image $data_file $addr $size
}
