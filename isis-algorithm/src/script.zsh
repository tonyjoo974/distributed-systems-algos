#!/bin/sh

#cmd="ls -la $APPROOTDIR | grep exception"

user=$2
pass=$3

fileName3="*.py config_*"
fileName=$fileName3
hostCount=$4
currentHost=""

createDir()
{
    for i in $(seq 1 $hostCount); 
    do 
        port="077"
        runScript="python3 -u gentx.py 5 | python3 mp1_node.py node$i $i$port config_${i}_${hostCount}.txt"
        runScriptFile="run_${i}.sh"
        currentHost="fa21-cs425-g47-0$i.cs.illinois.edu"
        #echo $runScript > run.sh
        createDirInternal &
    done
}

createDirInternal()
{
    sshpass -p $pass ssh -o StrictHostKeyChecking=no $user@$currentHost mkdir mp1
    echo "Making MP1 dir to $currentHost done"    
    echo $runScript > $runScriptFile
    sshpass -p $pass scp -o StrictHostKeyChecking=no $runScriptFile $user@$currentHost:~/mp1 
    echo "Creating $runScriptFile for $currentHost done"
}

cpFile()
{
    for i in $(seq 1 $hostCount); 
    do 
        currentHost="fa21-cs425-g47-0$i.cs.illinois.edu"
        cpFileInternal &
    done
}

cpFileInternal()
{
    sshpass -p $pass scp  -o StrictHostKeyChecking=no $fileName $user@$currentHost:~/mp1 
    echo "Copying file to $currentHost done "
}

getDiff()
{
    for i in $(seq 1 $hostCount); 
    do 
        fileDiff1="_delivered_output.txt"
        fileDiff2="node$i$fileDiff1"
        dataFile="*_data.txt"
        debugFile="*_debug.txt"
        currentHost="fa21-cs425-g47-0$i.cs.illinois.edu"
        getDiffInternal &
    done
}

getDiffInternal()
{
    sshpass -p $pass scp -o StrictHostKeyChecking=no $user@$currentHost:~/mp1/$fileDiff2 .
    echo "get diff done for $currentHost"
    sshpass -p $pass scp -o StrictHostKeyChecking=no $user@$currentHost:~/mp1/$dataFile .
    echo "get data file done for $currentHost"
    sshpass -p $pass scp -o StrictHostKeyChecking=no $user@$currentHost:~/mp1/$debugFile .
    echo "get debug file done for $currentHost"
}

doDiff() {
    for i in $(seq 1 $hostCount); 
    do 
        for j in $(seq 1 $hostCount);
        do
            fileDiff1="node${i}_delivered_output.txt"
            fileDiff2="node${j}_delivered_output.txt"
            echo "running cmp ${fileDiff1} ${fileDiff2}"
            cmp $fileDiff1 $fileDiff2
        done
    done    
}


if [ -z $2 ]; then
  echo " NEED PARAM 2 password"
fi

if [ -z $3 ]; then
  echo " NEED PARAM 3 username"
fi

if [ -z $4 ]; then
  echo " NEED PARAM 4 hostcount"
fi

if [ -z $1 ]; then
    echo "NEED PARAM 1 [ createDir | cpFile | init | getDiff | doDiff]"
elif [ $1 = "createDir" ]; then 
    echo "createDir"
    createDir
elif [ $1 = "cpFile" ]; then
    echo "cpFile"
    cpFile
elif [ $1 = "init" ]; then
    echo "init"
elif [ $1 = "getDiff" ]; then
    echo "getDiff"
    getDiff
elif [ $1 = "doDiff" ]; then
    echo "doDiff"
    doDiff
else
    echo "NEED PARAM 1 [ mkDir | cpFile | init | getDiff | doDiff]"
fi