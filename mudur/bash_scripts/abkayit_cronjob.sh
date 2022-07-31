#!/bin/bash

while [[ $# -gt 1 ]]
do
key="$1"

case $key in
    -w|--workingdir)
    WORKINGDIR="$2"
    shift # past argument
    ;;
    -pv|--pvirtualenvdir)
    PVIRTUALENVDIR="$2"
    shift # past argument
    ;;
    -f|--function)
    FUNCTION="$2"
    shift # past argument
    ;;
    -h|--help)
    echo "
	HELP:
	    -w: --workingdir: Project's base directory
	    -pv: --pvirtualenvdir: Python virtualenv directory
	    -f: --file: Python file that will be executed
	" 
    shift # past argument
    ;;
esac
shift # past argument or value
done
if [ -n "${WORKINGDIR}" ]
then
echo WORKING DIR  = "${WORKINGDIR}"
echo PVIRTUALENVDIR = "${PVIRTUALENVDIR}"
echo FUNCTION = "${FUNCTION}"

if [ -z "${PVIRTUALENVDIR}" ]
then
  source "${PVIRTUALENVDIR}"/bin/activate
fi

python "${WORKINGDIR}"/mudur/send_scheduled_email.py "${WORKINGDIR}" "${FUNCTION}"
else
echo "!!!Some parameters missing!!!"
echo "
      -w: --workingdir: Project's base directory
      -f: --function: function to be run
      -pv: --pvirtualenvdir: Python virtualenv directory"
fi
