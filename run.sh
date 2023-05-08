cmd="python app.py"

pkill -f "$cmd"
cnt=`ps -ef | grep "$cmd" | wc -l`
if [ $cnt -lt 2 ];then 
    $cmd > test.log &
fi