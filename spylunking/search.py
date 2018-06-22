import re
import requests
import spylunking.get_session_key as get_session_key
import json
from xml.dom.minidom import parseString
from spylunking.consts import SUCCESS
from spylunking.consts import NOT_RUN
from spylunking.consts import ERR
from spylunking.utils import ppj
from spylunking.log.setup_logging import \
    build_colorized_logger


log = build_colorized_logger(
    name="spylunking.search")


def search(
        user=None,
        password=None,
        token=None,
        address=None,
        query_dict=None,
        verify=False,
        debug=False):
    """search

    Search Splunk with a pre-built query dictionary and
    wait until it finishes.

    :param user: splunk username
    :param password: splunk password
    :param token: splunk token
    :param address: splunk HEC address: localhost:8089
    :param query_dict: query dictionary to search
    :param verify: ssl verify
    :param debug: debug flag
    """

    response_dict = None
    res = {
        'status': NOT_RUN,
        'err': '',
        'record': response_dict
    }
    try:
        url = 'https://{}'.format(
            address)

        if not token:
            try:
                token = get_session_key.get_session_key(
                    user=user,
                    password=password,
                    url=url,
                    verify=verify)
            except Exception as f:
                res['err'] = (
                    'Failed to get splunk token for user={} url={} '
                    'ex={}').format(
                        user,
                        url,
                        f)
                res['status'] = ERR
                return res
        # end of trying to login to get a valid token

        auth_header = {
            'Authorization': 'Splunk {}'.format(
                token)
        }
        search_url = '{}/services/search/jobs'.format(
            url)

        search_job = requests.post(
            url=search_url,
            headers=auth_header,
            verify=verify,
            data=query_dict
        )

        job_id = None
        try:
            job_id = parseString(
                search_job.text).getElementsByTagName(
                    'sid')[0].childNodes[0].nodeValue
        except Exception as e:
            log.error((
                'Failed searching splunk response={} for '
                'query={} url={} '
                'ex={}').format(
                    search_job.text,
                    ppj(query_dict),
                    search_url,
                    e))
        # end of try/ex for search

        if job_id:
            # Step 3: Get the search status
            search_status_url = '{}/services/search/jobs/{}/'.format(
                url,
                job_id)
            isnotdone = True
            while isnotdone:
                searchstatus = requests.get(
                    url=search_status_url,
                    verify=verify,
                    headers=auth_header)
                isdonestatus = re.compile('isDone">(0|1)')
                isdonestatus = isdonestatus.search(
                    searchstatus.text).groups()[0]
                if (isdonestatus == '1'):
                    isnotdone = False

            # Step 4: Get the search results
            job_url = (
                '{}/services/search/jobs/{}/'
                'results?output_mode=json&count=0').format(
                    url,
                    job_id)
            search_results = requests.get(
                job_url,
                verify=verify,
                headers=auth_header)
            if debug:
                log.info(
                    'search {}\nresults:\n[{}]'.format(
                        query_dict,
                        search_results.text))

            response_dict = None
            try:
                response_dict = json.loads(search_results.text)
            except Exception as e:
                log.error((
                    'Failed to load json from search_results.text={} '
                    'url={} '
                    'ex={}').format(
                        search_results.text,
                        job_url,
                        e))

        res["status"] = SUCCESS
        res["err"] = ""
        res["record"] = response_dict
    except Exception as e:
        res["err"] = (
            'Failed searching user={} url={} query={} '
            'ex={}').format(
                user,
                query_dict,
                e)
        res["status"] = ERR
        log.error(res["err"])
    # end of try/ex

    return res
# end of search
