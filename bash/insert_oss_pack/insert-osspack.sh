#!/bin/bash

#=============================================================================
OSSPACK_DIR=/var/versa/packages/osspack


usage()
{
    cat <<EOF
Usage: $(basename $0) --file <filename> --subs [flex] --ver <osspack_version>
All parameters are required
EOF
    exit 0
}

#=============================================================================
create_n_update_postgres() {
    local pkg_name=$1
    local product=$2
    local version=$3
    local len=$4
    local mdate=$5
    # Hard coded stuff
    local os_version="bionic"
    local upd_type="full"
    local percent="100"
    local dwnld_st="Download_Succeed",
sudo -u postgres psql -d vnms <<-EOF
insert into osspack_device_updates( package_name, product, os_version, update_type,
        version, size, percentage, status, download_time,
        create_date, modify_date, lastupdatedby)
values('${pkg_name}', '${product}', ${os_version}, ${upd_type},
        '${version}', '$len', $percent, ${dwnld_st}, to_timestamp('${mdate}', 'yyyy-mm-dd-hh24:mi:ss'), 
        to_timestamp('${mdate}', 'yyyy-mm-dd-hh24:mi:ss'), to_timestamp('${mdate}', 'yyyy-mm-dd-hh24:mi:ss'), 'Administrator');
EOF
}

#=============================================================================
file_details() {
    local subs=$1
    local fname=$2
    local vers=$3
    full_fname="${OSSPACK_DIR}"/"$subs"/$subs"-osspack-"$vers"-bionic.bin"
    #echo ${full_fname}
    mv $fname ${full_fname}
    chown versa:versa ${full_fname}
    chmod 644 ${full_fname}
    declare -a arr

    # the bracket before the dollar sign splits into words
    arr=($(stat -c"%U %s %Z" ${full_fname})) 
    retVal=$?
    if [ $retVal -ne 0 ]; then 
        echo "Can not stat ${full_fname}" 
        exit $retVal
    fi

    mdate=$(date -d @"${arr[2]}" +'%Y-%m-%d-%H:%M:%S')
    #create_n_update_postgres(pkg_name,product,version,size,date)
    create_n_update_postgres $(basename ${full_fname}) $subs $vers "${arr[1]}" $mdate

}

#=============================================================================
if [ "$EUID" -ne 0 ]; then
    echo  "Please run as root"
    exit -1
fi

while [ $# -gt 0 ]; do
    case "$1" in
        -h|-help|--help)
            usage
            ;;
        --subs)
            case "$2" in 
                flex*) subsystem="versa-flexvnf"; ;;
                dir*) subsystem="versa-director"; ;;
                anal*) subsystem="versa-analytics"; ;;
                *) echo "wrong subsystem"
                usage
                ;;
            esac
            ;;
        --file)
            fname=$2
            if [ -r $2 ]  &&  [ -f $2 ]; then 
                fname=$2
            else
                echo "File=$2 does not exist or is not readable "
                exit -1 
            fi
            ;;
        --ver)
            vers=$2
            ;;
    esac
    shift
done

if [ -z ${subsystem+x} ] || [ -z ${fname+x} ] || [ -z ${vers+x} ]; then
    echo "command line parameters not set correctly"
    usage
fi


file_details $subsystem $fname $vers

exit 0
