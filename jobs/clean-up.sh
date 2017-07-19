# run this from the logs directory

cd $HOME/GPnetworks/logs

floatToint() {
    printf "%.0f\n" "$@"
}
ls ./ | egrep -o fit-region.o[0-9]+ | uniq > tmp

while read line
do
    ENTROPY=9999999999
    unset PICKED_PPC
    unset PICKED_BLOCKSTATE
    for f in $line*
    do
    if egrep -q Entropy $f
    then
        NEW_ENT="$(egrep Entropy $f | egrep -o [0-9\\.]+)"
        NEW_ENT="$(floatToint $NEW_ENT)"
        if [ $NEW_ENT -le $ENTROPY ]
        then
            ENTROPY=$NEW_ENT
            PICKED_PPC="$(egrep "Saving PPCs to" $f | sed "s/Saving PPCs to //")"
            PICKED_BLOCKSTATE="$(egrep "Saving blockstate to" $f | sed "s/Saving blockstate to //")"
        fi
    else
        echo "Entropy not found in" $f
    fi
    done
    echo $PICKED_PPC
    echo $PICKED_BLOCKSTATE
    echo $ENTROPY
    echo $PICKED_PPC | sed '/^\s*$/d' >> selected-PPCs
    echo $PICKED_BLOCKSTATE | sed '/^\s*$/d' >> selected-blockstates
done < tmp
rm tmp
cat selected-PPCs | sort > selected-PPCs.txt
rm selected-PPCs
cat selected-blockstates | sort > selected-blockstates.txt
rm selected-blockstates

# move PPCs
while read line
do
    FILENAME="$(echo $line | sed "s/.*\///")"
    cp $line /srv/scratch/ppcs/PPCs/$FILENAME
done < selected-PPCs.txt
rm selected-PPCs.txt

#blockstates and logs
while read line
do
    FILENAME="$(echo $line | sed "s/.*\///")"
    cp $line /srv/scratch/ppcs/blockstates/$FILENAME
    cp $line.log /srv/scratch/ppcs/blockstates/$FILENAME.log
done < selected-blockstates.txt
rm selected-blockstates.txt
rm *
rm -rf /srv/scratch/ppcs/out
