#!/bin/sh

SLEEPINT=$1
if [ -z "$SLEEPINT" ]; then
    SLEEPINT=4
fi

export SS_XAPP=`kubectl get svc -n ricxapp --field-selector metadata.name=service-ricxapp-ss-nbi -o jsonpath='{.items[0].spec.clusterIP}'`
if [ -z "$SS_XAPP" ]; then
    export SS_XAPP=`kubectl get svc -n ricxapp --field-selector metadata.name=service-ricxapp-ss-rmr -o jsonpath='{.items[0].spec.clusterIP}'`
fi
if [ -z "$SS_XAPP" ]; then
    echo "ERROR: failed to find ss-xapp nbi service; aborting!"
    exit 1
fi

echo SS_XAPP=$SS_XAPP ; echo

echo Listing NodeBs: ; echo
curl -i -X GET http://${SS_XAPP}:8000/v1/nodebs ; echo ; echo
echo Listing Slices: ; echo
curl -i -X GET http://${SS_XAPP}:8000/v1/slices ; echo ; echo
echo Listing Ues: ; echo
curl -i -X GET http://${SS_XAPP}:8000/v1/ues ; echo ; echo

sleep $SLEEPINT

echo "Creating NodeB (id=1):" ; echo
OUTPUT=`curl -X POST -H "Content-type: application/json" -d '{"type":"eNB","id":411,"mcc":"001","mnc":"01"}' http://${SS_XAPP}:8000/v1/nodebs`
echo $OUTPUT
NBNAME=`echo $OUTPUT | jq -r '.name'`
echo Listing NodeBs: ; echo
curl -i -X GET http://${SS_XAPP}:8000/v1/nodebs ; echo ; echo

if [ -z "$OUTPUT" -o -z "$NBNAME" ]; then
    echo "ERROR: failed to create NodeB; aborting"
    exit 1
fi

sleep $SLEEPINT

echo "Creating Slice (name=fast)": ; echo
curl -i -X POST -H "Content-type: application/json" -d '{"name":"fast","allocation_policy":{"type":"proportional","share":1024}}' http://${SS_XAPP}:8000/v1/slices ; echo ; echo
echo Listing Slices: ; echo
curl -i -X GET http://${SS_XAPP}:8000/v1/slices ; echo ; echo

sleep $SLEEPINT

echo "Creating Slice (name=slow)": ; echo
curl -i -X POST -H "Content-type: application/json" -d '{"name":"slow","allocation_policy":{"type":"proportional","share":256}}' http://${SS_XAPP}:8000/v1/slices ; echo ; echo
echo Listing Slices: ; echo
curl -i -X GET http://${SS_XAPP}:8000/v1/slices ; echo ; echo

sleep $SLEEPINT

echo "Binding Slice to NodeB (name=fast):" ; echo
curl -i -X POST http://${SS_XAPP}:8000/v1/nodebs/${NBNAME}/slices/fast ; echo ; echo
echo "Getting NodeB (name=${NBNAME}):" ; echo
curl -i -X GET http://${SS_XAPP}:8000/v1/nodebs/${NBNAME} ; echo ; echo

sleep $SLEEPINT

echo "Binding Slice to NodeB (name=slow):" ; echo
curl -i -X POST http://${SS_XAPP}:8000/v1/nodebs/${NBNAME}/slices/slow ; echo ; echo
echo "Getting NodeB (name=${NBNAME}):" ; echo
curl -i -X GET http://${SS_XAPP}:8000/v1/nodebs/${NBNAME} ; echo ; echo

sleep $SLEEPINT

echo "Creating Ue (ue=001010123456789)" ; echo
curl -i -X POST -H "Content-type: application/json" -d '{"imsi":"001010123456789"}' http://${SS_XAPP}:8000/v1/ues ; echo ; echo
echo Listing Ues: ; echo
curl -i -X GET http://${SS_XAPP}:8000/v1/ues ; echo ; echo

sleep $SLEEPINT

echo "Binding Ue to Slice fast (imsi=001010123456789):" ; echo
curl -i -X POST http://${SS_XAPP}:8000/v1/slices/fast/ues/001010123456789 ; echo ; echo
echo "Getting Slice (name=fast):" ; echo
curl -i -X GET http://${SS_XAPP}:8000/v1/slices/fast ; echo ; echo

#echo "Creating Ue (ue=001010123456788)" ; echo
#curl -i -X POST -H "Content-type: application/json" -d '{"imsi":"001010123456788"}' http://${SS_XAPP}:8000/v1/ues ; echo ; echo
#echo Listing Ues: ; echo
#curl -i -X GET http://${SS_XAPP}:8000/v1/ues ; echo ; echo

#echo "Binding Ue (imsi=001010123456788):" ; echo
#curl -i -X POST http://${SS_XAPP}:8000/v1/slices/slow/ues/001010123456788 ; echo ; echo
#echo "Getting Slice (name=slow):" ; echo
#curl -i -X GET http://${SS_XAPP}:8000/v1/slices/slow ; echo ; echo

#sleep $SLEEPINT

#echo "Inverting priority of fast and slow slices:" ; echo

#curl -i -X PUT -H "Content-type: application/json" -d '{"allocation_policy":{"type":"proportional","share":1024}}' http://${SS_XAPP}:8000/v1/slices/slow ; echo ; echo ;

#sleep $SLEEPINT

#curl -i -X PUT -H "Content-type: application/json" -d '{"allocation_policy":{"type":"proportional","share":256}}' http://${SS_XAPP}:8000/v1/slices/fast ; echo ; echo

#creation of nodeb, ues, slices and binding
