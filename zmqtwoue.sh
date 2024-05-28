#!/bin/sh

SLEEPINT=5;

export SS_XAPP=`kubectl get svc -n ricxapp --field-selector metadata.name=service-ricxapp-ss-rmr -o jsonpath='{.items[0].spec.clusterIP}'`
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
curl -i -X POST -H "Content-type: application/json" -d '{"type":"eNB","id":411,"mcc":"001","mnc":"01"}' http://${SS_XAPP}:8000/v1/nodebs ; echo ; echo
echo Listing NodeBs: ; echo
curl -i -X GET http://${SS_XAPP}:8000/v1/nodebs ; echo ; echo

sleep $SLEEPINT

echo "Creating Slice (name=fast)": ; echo
curl -i -X POST -H "Content-type: application/json" -d '{"name":"fast","allocation_policy":{"type":"proportional","share":1024}}' http://${SS_XAPP}:8000/v1/slices ; echo ; echo
echo Listing Slices: ; echo
curl -i -X GET http://${SS_XAPP}:8000/v1/slices ; echo ; echo

sleep $SLEEPINT

echo "Creating Slice (name=secure_slice)": ; echo
curl -i -X POST -H "Content-type: application/json" -d '{"name":"secure_slice","allocation_policy":{"type":"proportional","share":0}}' http://${SS_XAPP}:8000/v1/slices ; echo ; echo
echo Listing Slices: ; echo
curl -i -X GET http://${SS_XAPP}:8000/v1/slices ; echo ; echo

sleep $SLEEPINT

echo "Binding Slice to NodeB (name=fast):" ; echo

curl -i -X POST http://${SS_XAPP}:8000/v1/nodebs/enB_macro_001_001_0019b0/slices/fast ; echo ; echo
echo "Getting NodeB (name=enB_macro_001_001_0019b0):" ; echo
curl -i -X GET http://${SS_XAPP}:8000/v1/nodebs/enB_macro_001_001_0019b0 ; echo ; echo

sleep $SLEEPINT

echo "Binding Slice to NodeB (name=secure_slice):" ; echo

curl -i -X POST http://${SS_XAPP}:8000/v1/nodebs/enB_macro_001_001_0019b0/slices/secure_slice ; echo ; echo
echo "Getting NodeB (name=enB_macro_001_001_0019b0):" ; echo
curl -i -X GET http://${SS_XAPP}:8000/v1/nodebs/enB_macro_001_001_0019b0 ; echo ; echo

sleep $SLEEPINT

echo "Creating Ue (ue=001010123456789)" ; echo
curl -i -X POST -H "Content-type: application/json" -d '{"imsi":"001010123456789"}' http://${SS_XAPP}:8000/v1/ues ; echo ; echo
echo Listing Ues: ; echo
curl -i -X GET http://${SS_XAPP}:8000/v1/ues ; echo ; echo

sleep $SLEEPINT

echo "Creating Ue (ue=001010123456780)" ; echo
curl -i -X POST -H "Content-type: application/json" -d '{"imsi":"001010123456780"}' http://${SS_XAPP}:8000/v1/ues ; echo ; echo
echo Listing Ues: ; echo
curl -i -X GET http://${SS_XAPP}:8000/v1/ues ; echo ; echo

sleep $SLEEPINT

echo "Binding Ue to Slice fast (imsi=001010123456789):" ; echo
curl -i -X POST http://${SS_XAPP}:8000/v1/slices/fast/ues/001010123456789 ; echo ; echo
echo "Getting Slice (name=fast):" ; echo
curl -i -X GET http://${SS_XAPP}:8000/v1/slices/fast ; echo ; echo

echo "Binding Ue (imsi=001010123456780):" ; echo
curl -i -X POST http://${SS_XAPP}:8000/v1/slices/fast/ues/001010123456780 ; echo ; echo
echo "Getting Slice (name=fast):" ; echo
curl -i -X GET http://${SS_XAPP}:8000/v1/slices/fast; echo ; echo

#creation of nodeb, ues, slices and binding
