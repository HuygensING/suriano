#!/bin/zsh

HELP="Provision the PVC on k8s

USAGE

./provision.sh task

Arguments

task: inspect|files|images|all
    inspect
        open a ssh shell on the target machine
    watm
        copy the watm to the team text VM
    files
        copy the manifests and other static files (not the page images)
    images
        copy the page images (not the manifests and other static files)
    all
        copy page images, manifests, and other static files
"

if [[ "$1" == "--help" && "$1" == "-h" && "$1" == "-?" ]]; then
    printf "$HELP"
    exit
fi

task=$1

if [[ -z $task ]]; then
    printf "Pass task argument.\n"
    printf "For more info pass --help\n"
    exit
fi
if [[ "$task" != "inspect" && "$task" != "watm" && "$task" != "files" && "$task" != "images" && "$task" != "all" ]]; then
    printf "task argument should be watm or files or images or all\n"
    printf "For more info pass --help\n"
    exit
fi
shift

# load the k-suite:
# https://code.huc.knaw.nl/tt/smart-k8s/-/blob/main/docs/k-suite.md

function k {
    if [[ "$1" == "" ]]; then
        source ~/code.huc.knaw.nl/tt/smart-k8s/scripts/k8s.sh
        echo "k-suite enabled"
    else
        echo "First do k without arguments in order to load the k-suite"
    fi
}

k

imageInDir="scans"
kset suriano

kcd
latest=`cat watm/latest`
watmSrcDir="watm/$latest"
watmDstDir="data/deploy/suriano/$watmSrcDir"

source programs/env


if [[ "$task" == "all" || "$task" == "watm" ]]; then
    printf "WATM export version: $latest\n"
    exit
    ssh "$ttvmUser@$ttvmMachine" "mkdir -p /$watmDstDir"
    scp -pr "$watmSrcDir/prod" "$ttvmUser@$ttvmMachine:/$watmDstDir" 
fi

if [[ "$task" == "all" || "$task" == "images" ]]; then
    ktoc -c sidecar "$imageInDir" /data/imageroot
fi

if [[ "$task" == "all" || "$task" == "files" ]]; then
    cd static
    ktoc -c sidecar "prod" /data/files
    ktoc -c sidecar both /data/files
fi

if [[ "$task" == "inspect" ]]; then
    ssh "$ttvmUser@$ttvmMachine"
fi
