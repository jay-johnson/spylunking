#!/bin/bash

log_type="$1"

action="docker"
if [[ "${log_type}" == "s" ]]; then
    action="service"
elif [[ "${log_type}" == "d" ]]; then
    action="docker"
else
    action="docker"
fi

if [[ "${action}" == "service" ]]; then
    echo "pulling service logs"
    docker exec -it splunk cat /opt/splunk/service.log
elif [[ "${action}" == "docker" ]]; then
    echo "pulling docker logs"
    docker logs splunk
else
    echo "tailing docker logs"
    docker logs -f splunk
fi

exit 0
