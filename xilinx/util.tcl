# handles the exception of no files
proc glob_wo_error { pattern } {
	if [ catch { set temp [glob $pattern] } msg ] {
		set result {}
	} else {
		set result $temp
	}
	return $result
}

proc concat_file_list { conv_list pattern} {
	return [concat $conv_list [glob_wo_error $pattern]]
}

proc touch { path } {
	if {[file exist $path]==0} {
		close [open $path w]
	}
}

proc get_setup_wns {} {
	set path [get_timing_paths -setup -max_paths 1 -nworst 1]
	if {$path eq ""} {
		return 0
	}
	return [get_property SLACK $path]
}
