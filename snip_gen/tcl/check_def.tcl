foreach lef $::env(LEF_FILES) {
    read_lef $lef
}

read_def $::env(DEF_FILE)
