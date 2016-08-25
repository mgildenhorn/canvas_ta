'''
Modular Input Script

Copyright (C) 2012 Splunk, Inc.
All Rights Reserved

'''

import sys,logging,os,time,re,threading
import os.path
import ConfigParser
import xml.dom.minidom
#import tokens
from datetime import datetime


SPLUNK_HOME = os.environ.get("SPLUNK_HOME")

RESPONSE_HANDLER_INSTANCE = None
SPLUNK_PORT = 8089
STANZA = None
SESSION_TOKEN = None
REGEX_PATTERN = None

#dynamically load in any eggs in /etc/apps/snmp_ta/bin
#EGG_DIR = SPLUNK_HOME + "/etc/apps/canvas_ta/bin/"
#EGG_DIR = SPLUNK_HOME + "/etc/apps/" + appname + "/bin/"

EGG_DIR = os.path.dirname(os.path.abspath(__file__)) + "/"



for filename in os.listdir(EGG_DIR):
    if filename.endswith(".egg"):
        sys.path.append(EGG_DIR + filename) 
       
import requests,json
from requests.auth import HTTPBasicAuth
from requests.auth import HTTPDigestAuth
from requests_oauthlib import OAuth1
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import WebApplicationClient 
from requests.auth import AuthBase
from splunklib.client import connect
from splunklib.client import Service
from croniter import croniter
           
#set up logging
logging.root
#logging.root.setLevel(logging.ERROR)
logging.root.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s %(message)s')
#with zero args , should go to STD ERR
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logging.root.addHandler(handler)

#logging.info("here we are")

addon_path = os.path.dirname(os.path.abspath(__file__))
addon_path = os.path.abspath(os.path.join(addon_path,os.pardir))
#logging.info ("Addon Path is: %s" % addon_path)


SCHEME = """<scheme>
    <title>Canvas</title>
    <description>Input for collecting data from the Instructure Canvas LMS</description>
    <use_external_validation>true</use_external_validation>
    <streaming_mode>xml</streaming_mode>
    <use_single_instance>false</use_single_instance>

    <endpoint>
        <args>    
            <arg name="name">
                <title>REST input name</title>
                <description>Name of this REST input</description>
            </arg>
                   
            <arg name="request_payload">
                <title>Request Payload</title>
                <description>Request payload for POST and PUT HTTP Methods</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="streaming_request">
                <title>Streaming Request</title>
                <description>Whether or not this is a HTTP streaming request : true | false</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="http_proxy">
                <title>HTTP Proxy Address</title>
                <description>HTTP Proxy Address</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="https_proxy">
                <title>HTTPs Proxy Address</title>
                <description>HTTPs Proxy Address</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="request_timeout">
                <title>Request Timeout</title>
                <description>Request Timeout in seconds</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="backoff_time">
                <title>Backoff Time</title>
                <description>Time in seconds to wait for retry after error or timeout</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="polling_interval">
                <title>Polling Interval</title>
                <description>Interval time in seconds to poll the endpoint</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="sequential_mode">
                <title>Sequential Mode</title>
                <description>Whether multiple requests spawned by tokenization are run in parallel or sequentially</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="sequential_stagger_time">
                <title>Sequential Stagger Time</title>
                <description>An optional stagger time period between sequential requests</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="delimiter">
                <title>Delimiter</title>
                <description>Delimiter to use for any multi "key=value" field inputs</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="index_error_response_codes">
                <title>Index Error Responses</title>
                <description>Whether or not to index error response codes : true | false</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="response_filter_pattern">
                <title>Response Filter Pattern</title>
                <description>Python Regex pattern, if present , responses must match this pattern to be indexed</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="custom_auth_handler">
                <title>Custom_Auth Handler</title>
                <description>Python classname of custom auth handler</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="custom_auth_handler_args">
                <title>Custom_Auth Handler Arguments</title>
                <description>Custom Authentication Handler arguments string ,  key=value,key2=value2</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
            <arg name="cookies">
                <title>Cookies</title>
                <description>Persist cookies in format key=value,key2=value2,...</description>
                <required_on_edit>false</required_on_edit>
                <required_on_create>false</required_on_create>
            </arg>
        </args>
    </endpoint>
</scheme>
"""

def get_current_datetime_for_cron():
    current_dt = datetime.now()
    #dont need seconds/micros for cron
    current_dt = current_dt.replace(second=0, microsecond=0)
    return current_dt
            
def do_validate():
    config = get_validation_config() 
    #TODO
    #if error , print_validation_error & sys.exit(2) 
    
def stanza_params_saved(file):
    if os.path.isfile(file):
        return True
    else:
        return False
    #logging.info("File is: %s" % file)

def get_url_args(required_params,stanzaconfigfile):
    #requiredfile = SPLUNK_HOME + '/etc/apps/canvas_ta/bin/required.cfg'
    #stanzafile = SPLUNK_HOME + '/etc/apps/canvas_ta/local/' + STANZA[9:] + '.cfg'
    addon_path = os.path.dirname(os.path.abspath(__file__))
    addon_path = os.path.abspath(os.path.join(addon_path,os.pardir))
    stanzafile = addon_path + '/local/' + stanzaconfigfile + '.cfg'
    #stanzafile = SPLUNK_HOME + '/etc/apps/canvas_ta/local/' + stanzaconfigfile + '.cfg'
    url_args = {}
    stanza_present = False

    #required_config = ConfigParser.RawConfigParser()
    #required_config.read(requiredfile)
    if stanza_params_saved(stanzafile):
        #logging.info('Stanza File PRESENT')
        stanza_present = True
        stanza_config = ConfigParser.RawConfigParser()
        stanza_config.read(stanzafile)
    #else:
        #logging.info('Stanza File NOT PRESENT')
    if STANZA[9:] == 'auth_logs':
        #url_args["per_page"] = required_config.get('Common','per_page')
        url_args["per_page"] = required_params["per_page"]
        if stanza_present:
            try:
                url_args["start_time"] = stanza_config.get('url_args','start_time')
                url_args["end_time"] = stanza_config.get('url_args','end_time')
                if url_args["start_time"] == '' or url_args["end_time"] == '':
                    logging.error("%s start_time or end_time is empty" % STANZA[9:])
                    sys.exit(2)
            except ConfigParser.NoOptionError:
                logging.error("%s start_time or end_time is missing" % STANZA[9:])
                sys.exit(2)
        else:
            #url_args["start_time"] = required_config.get('Initial','start_time')
            #url_args["end_time"] = required_config.get('Initial','end_time')
            url_args["start_time"] = required_params["start_time"]
            url_args["end_time"] = required_params["end_time"]
            if url_args["start_time"] == '' or url_args["end_time"] == '' or url_args["start_time"] == 'YYYY-MM-DD' or url_args["end_time"] == 'YYYY-MM-DD':
                #throw up because it is expecting values here
                logging.error("Initial start_time and end_time values missing FROM *** /etc/apps/canvas_ta/local/canvas.conf ***")
                sys.exit(2)
    startmatch = (re.search('^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$',url_args["start_time"]) or re.search('^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$',url_args["start_time"]) or re.search('^\d{4}-\d{2}-\d{2}$',url_args["start_time"]))
    endmatch = (re.search('^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$',url_args["end_time"]) or re.search('^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$',url_args["end_time"]) or re.search('^\d{4}-\d{2}-\d{2}$',url_args["end_time"]))
    if (startmatch is None) or (endmatch is None):
        #logging.info("Match will fail
    #if (re.search('^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$',url_args["start_time"]) or re.search('^\d{4}-\d{2}-\d{2}$',url_args["start_time"])) and (re.search('^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$',url_args["end_time"]) or re.search('^\d{4}-\d{2}-\d{2}$',url_args["end_time"])) is None:
        logging.error("Date and Time not formatted properly")
        sys.exit(2)
    else:                   
        return url_args

def do_run(config,endpoint_list,required_params):
    
    #setup some globals
    server_uri = config.get("server_uri")
    global SPLUNK_PORT
    global STANZA
    global SESSION_TOKEN 
    global delimiter
#    global counter
    SPLUNK_PORT = server_uri[18:]
    STANZA = config.get("name")
    SESSION_TOKEN = config.get("session_key")
        
    #params
    
    #http_method=config.get("http_method","GET")
    http_method='GET'
    request_payload=config.get("request_payload")
    
    #none | basic | digest | oauth1 | oauth2
    #auth_type=config.get("auth_type","none")
    auth_type='none'
    
    #Delimiter to use for any multi "key=value" field inputs
    delimiter=config.get("delimiter",",")
    
    #for basic and digest
    auth_user=config.get("auth_user")
    auth_password=config.get("auth_password")
    
    #for oauth1
    oauth1_client_key=config.get("oauth1_client_key")
    oauth1_client_secret=config.get("oauth1_client_secret")
    oauth1_access_token=config.get("oauth1_access_token")
    oauth1_access_token_secret=config.get("oauth1_access_token_secret")
    
    #for oauth2
    oauth2_token_type=config.get("oauth2_token_type","Bearer")
    oauth2_access_token=config.get("oauth2_access_token")
    
    oauth2_refresh_token=config.get("oauth2_refresh_token")
    oauth2_refresh_url=config.get("oauth2_refresh_url")
    oauth2_refresh_props_str=config.get("oauth2_refresh_props")
    oauth2_client_id=config.get("oauth2_client_id")
    oauth2_client_secret=config.get("oauth2_client_secret")
    
    oauth2_refresh_props={}
    if not oauth2_refresh_props_str is None:
        oauth2_refresh_props = dict((k.strip(), v.strip()) for k,v in 
              (item.split('=',1) for item in oauth2_refresh_props_str.split(delimiter)))
    oauth2_refresh_props['client_id'] = oauth2_client_id
    oauth2_refresh_props['client_secret'] = oauth2_client_secret
        
    http_header_propertys={}
    #http_header_propertys_str=config.get("http_header_propertys")
    # Canvas Header Override
    http_header_propertys_str='Authorization=Bearer $canvastoken$'
    #logging.info("Header Propertys String: %s" % http_header_propertys_str)
    if not http_header_propertys_str is None:
        http_header_propertys_str = replaceHeaderTokens(http_header_propertys_str,required_params)
        #logging.info("NEW Header Propertys String: %s " % http_header_propertys_str)
        http_header_propertys = dict((k.strip(), v.strip()) for k,v in 
              (item.split('=',1) for item in http_header_propertys_str.split(delimiter)))
        #logging.info("Header Propertys Dict: %s" % http_header_propertys)

# This is where the url_args are first grabbed from the inputs.conf
# TODO - If file exists, take url_args from it - if not, take from inputs.conf    

    #file = SPLUNK_HOME + '/etc/apps/canvas_ta/local/' + STANZA[9:] + '.cfg'
    
    #if stanza_params_saved(file):
    #    #logging.error("File exists")        
    #    url_config = ConfigParser.RawConfigParser()
    #    url_config.read(file)
    #    url_args_str = url_config.get(STANZA[9:],'url_args')        
        # Read config file, and load url_args into url_args_str
    #else:
    #    url_args_str=config.get("url_args")
        #logging.error("No File exists")
        # Read config from inputs.conf

    ###url_args={} 
    #commented out for file method
    #url_args_str=config.get("url_args")
    
    #logging.info("URL Args: %s" % url_args_str)
    
    # Getting URL Args from file now, so commenting this out
    #if not url_args_str is None:
    #    url_args = dict((k.strip(), v.strip()) for k,v in 
    #          (item.split('=',1) for item in url_args_str.split(delimiter)))
    ###url_args = get_url_args(required_params)
        
    #json | xml | text    
    #response_type=config.get("response_type","json")
    response_type='json'
    
    streaming_request=int(config.get("streaming_request",0))
    
    http_proxy=config.get("http_proxy")
    https_proxy=config.get("https_proxy")
    
    proxies={}
    
    if not http_proxy is None:
        proxies["http"] = http_proxy   
    if not https_proxy is None:
        proxies["https"] = https_proxy 
        
    cookies={} 
    cookies_str=config.get("cookies")
    if not cookies_str is None:
        cookies = dict((k.strip(), v.strip()) for k,v in 
              (item.split('=',1) for item in cookies_str.split(delimiter)))
        
    request_timeout=int(config.get("request_timeout",30))
    
    backoff_time=int(config.get("backoff_time",10))
    
    sequential_stagger_time  = int(config.get("sequential_stagger_time",0))
    
    polling_interval_string = config.get("polling_interval","600")
    
    options = {}
    # Will the user data be merged into the raw event
    options["mergeUsers"] = required_params["merge_users"]
    options["mergeLogins"] = required_params["merge_logins"]
    options["mergeAccts"] = required_params["merge_accts"]
    options["mergePageViews"] = required_params["merge_pageviews"]
    
    canvasauthhandler = 'CanvasAuthLogHandler'
        
    #polling_interval_string = config.get("polling_interval","*/1 * * * *")
       
# MG - Disable digit polling due to current issue
#    if polling_interval_string.isdigit():
#        polling_interval_string = "*/1 * * * *"   
    skip_first = False
    first_run = True
         
    if polling_interval_string.isdigit():
        polling_type = 'interval'
        polling_interval=int(polling_interval_string)   
    else:
        polling_type = 'cron'
        if '*/' in polling_interval_string:
            #logging.info("Will Skip First")
            skip_first = True
        else:
            #logging.info("Will Not Skip First")
            cron_start_date = datetime.now()
            cron_iter = croniter(polling_interval_string, cron_start_date)
    
    index_error_response_codes=int(config.get("index_error_response_codes",0))
    
    response_filter_pattern=config.get("response_filter_pattern")
    
    if response_filter_pattern:
        global REGEX_PATTERN
        REGEX_PATTERN = re.compile(response_filter_pattern)
        
    response_handler_args={} 
    #response_handler_args_str=config.get("response_handler_args")
    response_handler_args_str=None
    if not response_handler_args_str is None:
        response_handler_args = dict((k.strip(), v.strip()) for k,v in 
              (item.split('=',1) for item in response_handler_args_str.split(delimiter)))
        
    #response_handler=config.get("response_handler","DefaultResponseHandler")
    #if STANZA[9:] is auth_logs, then set response_handler = 'CanvasAuthLogHandler'
    #if STANZA[9:] is users_lookup, then set response_handler = 'CanvasUsersLookupHandler'
#    handlers = {'auth_logs': 'CanvasAuthLogHandler', 'users_lookup': 'CanvasUsersLookupHandler'}
#    handlers = {'auth_logs': 'CanvasAuthMergeLogHandler', 'users_lookup': 'CanvasUsersLookupHandler'}
    handlers = {'auth_logs': canvasauthhandler}
    
    try:
        response_handler=handlers[STANZA[9:]]
    except KeyError:
        logging.error("Stanza %s is not a supported stanza. Only auth_logs is supported today." % STANZA[9:])
        sys.exit(2)
    #logging.info("handler is: %s" % response_handler)
    module = __import__("responsehandlers")
    class_ = getattr(module,response_handler)

    global RESPONSE_HANDLER_INSTANCE
    RESPONSE_HANDLER_INSTANCE = class_(**response_handler_args)
   
    custom_auth_handler=config.get("custom_auth_handler")
    
    if custom_auth_handler:
        module = __import__("authhandlers")
        class_ = getattr(module,custom_auth_handler)
        custom_auth_handler_args={} 
        custom_auth_handler_args_str=config.get("custom_auth_handler_args")
        if not custom_auth_handler_args_str is None:
            custom_auth_handler_args = dict((k.strip(), v.strip()) for k,v in (item.split('=',1) for item in custom_auth_handler_args_str.split(delimiter)))
        CUSTOM_AUTH_HANDLER_INSTANCE = class_(**custom_auth_handler_args)
    
    #skip_first = False
    #logging.info("Polling interval string: %s" % polling_interval_string)
    #if polling_type == 'cron':    
    #    if '/' in polling_interval_string:
    #        logging.info("Will Skip First")
    #        skip_first = True
    #    else:
    #        cron_start_date = datetime.now()
    #        cron_iter = croniter(polling_interval_string, cron_start_date)
                         
    #counter += 1
    #logging.info("COUNT IS: %s" % counter)

        
    try: 
        auth=None
        oauth2=None
        if auth_type == "basic":
            auth = HTTPBasicAuth(auth_user, auth_password)
        elif auth_type == "digest":
            auth = HTTPDigestAuth(auth_user, auth_password)
        elif auth_type == "oauth1":
            auth = OAuth1(oauth1_client_key, oauth1_client_secret,
                  oauth1_access_token ,oauth1_access_token_secret)
        elif auth_type == "oauth2":
            token={}
            token["token_type"] = oauth2_token_type
            token["access_token"] = oauth2_access_token
            token["refresh_token"] = oauth2_refresh_token
            token["expires_in"] = "5"
            client = WebApplicationClient(oauth2_client_id)
            oauth2 = OAuth2Session(client, token=token,auto_refresh_url=oauth2_refresh_url,auto_refresh_kwargs=oauth2_refresh_props,token_updater=oauth2_token_updater)
        elif auth_type == "custom" and CUSTOM_AUTH_HANDLER_INSTANCE:
            auth = CUSTOM_AUTH_HANDLER_INSTANCE
   
        req_args = {"verify" : False ,"stream" : bool(streaming_request) , "timeout" : float(request_timeout)}

        if auth:
            req_args["auth"]= auth
        ###if url_args:
            ###req_args["params"]= url_args
        if cookies:
            req_args["cookies"]= cookies
        if http_header_propertys:
            #http_header_propertys = replaceHeaderTokens(http_header_propertys)
            req_args["headers"]= http_header_propertys
        if proxies:
            req_args["proxies"]= proxies
        if request_payload and not http_method == "GET":
            req_args["data"]= request_payload     
        
        mg_keep_going = False
                    
        while True:
            
            if not skip_first:                                         
                if not mg_keep_going:
                    if polling_type == 'cron':
                        next_cron_firing = cron_iter.get_next(datetime)
                        logging.info("Next PRE Cron Firing: %s" % next_cron_firing.strftime("%Y-%m-%dT%H:%M:%S"))
                        while get_current_datetime_for_cron() != next_cron_firing:
                            time.sleep(float(10))
            # Multiple Endpoints in set won't work for Canvas because they share the same updated params, so one set would override the other. If we implemented an array then maybe that would work.
            for endpoint in endpoint_list:  
                
                url_args = {}
                
                if STANZA[9:] == 'auth_logs':
                    accountidlist = re.findall("(?:/api/v1/audit/authentication/accounts/)(\d+)$",endpoint)
                    accountid = accountidlist[0]
                else:
                    accountid = ''
                stanzaconfigfile = STANZA[9:] + accountid

                # load url args for this endpoint if auth_logs is called. user_lookup doesn't need it.
                if STANZA[9:] == 'auth_logs':
                    url_args = get_url_args(required_params,stanzaconfigfile)
                elif STANZA[9:] == 'users_lookup':
                    url_args["per_page"] = required_params["per_page"]
                    
                if url_args:
                    req_args["params"]= url_args
                                    
                if "params" in req_args:
                    req_args_params_current = dictParameterToStringFormat(req_args["params"])
                else:
                    req_args_params_current = ""
                if "cookies" in req_args:
                    req_args_cookies_current = dictParameterToStringFormat(req_args["cookies"])
                else:
                    req_args_cookies_current = ""    
                if "headers" in req_args: 
                    req_args_headers_current = dictParameterToStringFormat(req_args["headers"])
                else:
                    req_args_headers_current = ""
                if "data" in req_args:
                    req_args_data_current = req_args["data"]
                else:
                    req_args_data_current = ""
                
                try:
                    if oauth2:
                        if http_method == "GET":
                            r = oauth2.get(endpoint,**req_args)
                        elif http_method == "POST":
                            r = oauth2.post(endpoint,**req_args) 
                        elif http_method == "PUT":
                            r = oauth2.put(endpoint,**req_args)       
                    else:
                        if http_method == "GET":
                            #logging.info("beginning endpoint request")
                            r = requests.get(endpoint,**req_args)
                            #logging.info("finished endpoint request")
                        elif http_method == "POST":
                            r = requests.post(endpoint,**req_args) 
                        elif http_method == "PUT":
                            r = requests.put(endpoint,**req_args) 
                        
                except requests.exceptions.Timeout,e:
                    logging.error("HTTP Request Timeout error: %s" % str(e))
                    time.sleep(float(backoff_time))
                    continue
                except Exception as e:
                    logging.error("Exception performing request: %s" % str(e))
                    time.sleep(float(backoff_time))
                    continue
                try:
                    #logging.info("Request Text: %s" % r.text)
                    #logging.info("Response Headers: %s" % r.headers)
                    #logging.info("Before raise for status")
                    r.raise_for_status()
                    #logging.info("After raise for status")
                    if streaming_request:
                        for line in r.iter_lines():
                            if line:
                                handle_output(r,line,response_type,req_args,endpoint,options)  
                        #continue
                    else:  
                        #logging.info("Getting Ready For calling the Response Handler")
                        #skip_first = False
                        mg_keep_going = False
                        #logging.info("beginning response handler")                
                        handle_output(r,r.text,response_type,req_args,endpoint,options)
                        #logging.info("finished response handler")
                        #adding continue to try
                        #continue
                except requests.exceptions.HTTPError,e:
                    error_output = r.text
                    error_http_code = r.status_code
                    if index_error_response_codes:
                        error_event=""
                        error_event += 'http_error_code = %s error_message = %s' % (error_http_code, error_output) 
                        print_xml_single_instance_mode(error_event)
                        sys.stdout.flush()
                    logging.error("HTTP Request error: %s" % str(e))
                    time.sleep(float(backoff_time))
                    #skip_first = False
                    mg_keep_going = True
                    continue

                if "params" in req_args:
                    checkParamUpdatedFile(req_args_params_current,dictParameterToStringFormat(req_args["params"]),req_args["params"],stanzaconfigfile)                
                # This section still may not work because of the continue
            #if "data" in req_args:   
            #    checkParamUpdated(req_args_data_current,req_args["data"],"request_payload")
            ###if "params" in req_args:
                #checkParamUpdatedFile(req_args_params_current,dictParameterToStringFormat(req_args["params"]),"url_args")
                ###checkParamUpdatedFile(req_args_params_current,dictParameterToStringFormat(req_args["params"]),req_args["params"])
                #logging.info("check param updated towards end")
            #if "headers" in req_args:
            #    checkParamUpdated(req_args_headers_current,dictParameterToStringFormat(req_args["headers"]),"http_header_propertys")
            #if "cookies" in req_args:
            #    checkParamUpdated(req_args_cookies_current,dictParameterToStringFormat(req_args["cookies"]),"cookies")

            # Sequential Stagger time won't be needed since we won't support multiple sets of entries                 
                if sequential_stagger_time > 0:
            #    logging.info("Sleeping %s for sequential stagger" % sequential_stagger_time)
                    time.sleep(float(sequential_stagger_time))
            #logging.info("We made it close to the end")
            
            if skip_first:
                if not mg_keep_going:
                    if polling_type == 'cron':
                        if first_run:
                            #logging.info("First Run Happening")
                            cron_start_date = datetime.now()
                            cron_iter = croniter(polling_interval_string, cron_start_date)
                            first_run = False
                        next_cron_firing = cron_iter.get_next(datetime)
                        logging.info("Next POST Cron Firing: %s" % next_cron_firing.strftime("%Y-%m-%dT%H:%M:%S"))
                        #skip_first = False
                        while get_current_datetime_for_cron() != next_cron_firing:
                            time.sleep(float(10))            
             #   skip_first = False
             #   cron_start_date = datetime.now()
             #   cron_iter = croniter(polling_interval_string, cron_start_date)
                
                
            if not mg_keep_going:       
                if polling_type == 'interval':
                    logging.info("Next Interval Time Coming For %s Seconds" % polling_interval)                         
                    time.sleep(float(polling_interval))
                    #logging.info("Finished Interval Time")
            
            #logging.info("I am hitting the end finally")
            
    except RuntimeError,e:
        logging.error("Looks like an error: %s" % str(e))
        sys.exit(2) 
          
def replaceHeaderTokens(raw_string,required_params):

    #requiredfile = SPLUNK_HOME + '/etc/apps/canvas_ta/bin/required.cfg'
    #if not stanza_params_saved(requiredfile):
    #required_config = ConfigParser.RawConfigParser()
    #required_config.read(requiredfile)
    
    try:
        http_header_propertys_list = [raw_string]
        #logging.info("Header Raw String: %s " % raw_string)
        #logging.error("Header Sub Before: %s " % http_header_propertys_list)
        substitution_tokens = re.findall("\$(?:\w+)\$",raw_string)
        #logging.info("Substitution Token: %s " % substitution_tokens)
        for token in substitution_tokens:
            #token_response = getattr(tokens,token[1:-1])()
            #token_response = required_config.get('Common',token[1:-1])
            token_response = required_params[token[1:-1]]
            #logging.info("token_response: %s" % token_response)
            if(isinstance(token_response,list)):
            #    temp_list = []
            #    for token_response_value in token_response:
            #        for header in http_header_propertys_list:
            #            temp_list.append(header.replace(token,token_response_value))
            #    http_header_propertys_list = temp_list
                #logging.info("Is Instance http_header_propertys_list: %s" % http_header_propertys_list)
                http_header_propertys_list_str = ''
            else:
                for index,header in enumerate(http_header_propertys_list):
                    http_header_propertys_list[index] = header.replace(token,token_response)
                #logging.info("Is Not List Instance http_header_propertys_list: %s" % http_header_propertys_list)
                for headerstring in http_header_propertys_list:
                    http_header_propertys_list_str = headerstring
        return http_header_propertys_list_str
    except:
        e = sys.exc_info()[1]
        logging.error("Looks like an error substituting tokens: %s" % str(e))


def replaceTokens(raw_string,required_params):

    #requiredfile = SPLUNK_HOME + '/etc/apps/canvas_ta/bin/required.cfg'
    #required_config = ConfigParser.RawConfigParser()
    #required_config.read(requiredfile)
    
    try:
        #logging.info("URL Before Made Into List: %s " % raw_string)
        url_list = [raw_string]
        #logging.info("URL Sub Before: %s " % url_list)   
        substitution_tokens = re.findall("\$(?:\w+)\$",raw_string)
        for token in substitution_tokens:
            # OLD METHOD FROM tokens File # token_response = getattr(tokens,token[1:-1])()
            #token_response = required_config.get('Common',token[1:-1])
            token_response = required_params[token[1:-1]]
            #logging.info("Token Response: %s" % token_response)
            # if accountid is a list
            if(isinstance(token_response,list)):   
                temp_list = []               
                for token_response_value in token_response:
                    for url in url_list:
                        temp_list.append(url.replace(token,token_response_value)) 
                url_list = temp_list
            else:
                for index,url in enumerate(url_list):
                    url_list[index] = url.replace(token,token_response)
        #logging.info("Token Sub: %s" % url_list)
        return url_list    
    except: 
        e = sys.exc_info()[1]
        logging.error("Looks like an error substituting tokens: %s" % str(e))  
                      	

def checkParamUpdated(cached,current,rest_name):
    
    #logging.info("cached = %s" % cached)
    #logging.info("current = %s" % current)
    if not (cached == current):
        try:
            args = {'host':'localhost','port':SPLUNK_PORT,'token':SESSION_TOKEN}
            service = Service(**args)   
            item = service.inputs.__getitem__(STANZA[9:])
            item.update(**{rest_name:current})
        except RuntimeError,e:
            logging.error("Looks like an error updating the modular input parameter %s: %s" % (rest_name,str(e),))   
        
                       
#def checkParamUpdatedFile(cached,current,rest_name):
def checkParamUpdatedFile(cached,current,url_args,stanzaconfigfile):
    #file = SPLUNK_HOME + '/etc/apps/canvas_ta/local/' + STANZA[9:] + '.cfg'
    addon_path = os.path.dirname(os.path.abspath(__file__))
    addon_path = os.path.abspath(os.path.join(addon_path,os.pardir))
    #file = SPLUNK_HOME + '/etc/apps/canvas_ta/local/' + stanzaconfigfile + '.cfg'
    file = addon_path + '/local/' + stanzaconfigfile + '.cfg'
    # update the file with the latest parameters
    if not (cached == current):
        url_config = ConfigParser.RawConfigParser()
        #url_config.add_section(STANZA[9:])
        url_config.add_section('url_args')
        if STANZA[9:] == 'auth_logs':
            url_config.set('url_args','start_time',url_args["start_time"])
            url_config.set('url_args','end_time',url_args["end_time"])    
        #url_config.set(STANZA[9:],'url_args',current)
        
        with open(file, 'wb') as configfile:
            url_config.write(configfile)
    

def dictParameterToStringFormat(parameter):
    
    if parameter:
        return ''.join(('{}={}'+delimiter).format(key, val) for key, val in parameter.items())[:-1] 
    else:
        return None
    
def oauth2_token_updater(token):
    
    try:
        args = {'host':'localhost','port':SPLUNK_PORT,'token':SESSION_TOKEN}
        service = Service(**args)   
        item = service.inputs.__getitem__(STANZA[9:])
        item.update(oauth2_access_token=token["access_token"],oauth2_refresh_token=token["refresh_token"])
    except RuntimeError,e:
        logging.error("Looks like an error updating the oauth2 token: %s" % str(e))

            
def handle_output(response,output,type,req_args,endpoint,options): 
    
    try:
        if REGEX_PATTERN:
            search_result = REGEX_PATTERN.search(output)
            if search_result == None:
                return   
        RESPONSE_HANDLER_INSTANCE(response,output,type,req_args,endpoint,options)
        sys.stdout.flush()               
    except RuntimeError,e:
        logging.error("Looks like an error handle the response output: %s" % str(e))

# prints validation error data to be consumed by Splunk
def print_validation_error(s):
    print "<error><message>%s</message></error>" % encodeXMLText(s)
    
# prints XML stream
def print_xml_single_instance_mode(s):
    print "<stream><event><data>%s</data></event></stream>" % encodeXMLText(s)
    
# prints simple stream
def print_simple(s):
    print "%s\n" % s

def encodeXMLText(text):
    text = text.replace("&", "&amp;")
    text = text.replace("\"", "&quot;")
    text = text.replace("'", "&apos;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text
  
def usage():
    print "usage: %s [--scheme|--validate-arguments]"
    logging.error("Incorrect Program Usage")
    sys.exit(2)

def do_scheme():
    print SCHEME

#read XML configuration passed from splunkd, need to refactor to support single instance mode
def get_input_config():
    config = {}

    try:
        # read everything from stdin
        config_str = sys.stdin.read()

        # parse the config XML
        doc = xml.dom.minidom.parseString(config_str)
        root = doc.documentElement
        
        session_key_node = root.getElementsByTagName("session_key")[0]
        if session_key_node and session_key_node.firstChild and session_key_node.firstChild.nodeType == session_key_node.firstChild.TEXT_NODE:
            data = session_key_node.firstChild.data
            config["session_key"] = data 
            
        server_uri_node = root.getElementsByTagName("server_uri")[0]
        if server_uri_node and server_uri_node.firstChild and server_uri_node.firstChild.nodeType == server_uri_node.firstChild.TEXT_NODE:
            data = server_uri_node.firstChild.data
            config["server_uri"] = data   
            
        conf_node = root.getElementsByTagName("configuration")[0]
        if conf_node:
            logging.debug("XML: found configuration")
            stanza = conf_node.getElementsByTagName("stanza")[0]
            if stanza:
                stanza_name = stanza.getAttribute("name")
                if stanza_name:
                    logging.debug("XML: found stanza " + stanza_name)
                    config["name"] = stanza_name

                    params = stanza.getElementsByTagName("param")
                    for param in params:
                        param_name = param.getAttribute("name")
                        logging.debug("XML: found param '%s'" % param_name)
                        if param_name and param.firstChild and \
                           param.firstChild.nodeType == param.firstChild.TEXT_NODE:
                            data = param.firstChild.data
                            config[param_name] = data
                            logging.debug("XML: '%s' -> '%s'" % (param_name, data))

        checkpnt_node = root.getElementsByTagName("checkpoint_dir")[0]
        if checkpnt_node and checkpnt_node.firstChild and \
           checkpnt_node.firstChild.nodeType == checkpnt_node.firstChild.TEXT_NODE:
            config["checkpoint_dir"] = checkpnt_node.firstChild.data

        if not config:
            raise Exception, "Invalid configuration received from Splunk."

        
    except Exception, e:
        raise Exception, "Error getting Splunk configuration via STDIN: %s" % str(e)

    return config

#read XML configuration passed from splunkd, need to refactor to support single instance mode
def get_validation_config():
    val_data = {}

    # read everything from stdin
    val_str = sys.stdin.read()

    # parse the validation XML
    doc = xml.dom.minidom.parseString(val_str)
    root = doc.documentElement

    logging.debug("XML: found items")
    item_node = root.getElementsByTagName("item")[0]
    if item_node:
        logging.debug("XML: found item")

        name = item_node.getAttribute("name")
        val_data["stanza"] = name

        params_node = item_node.getElementsByTagName("param")
        for param in params_node:
            name = param.getAttribute("name")
            logging.debug("Found param %s" % name)
            if name and param.firstChild and \
               param.firstChild.nodeType == param.firstChild.TEXT_NODE:
                val_data[name] = param.firstChild.data

    return val_data

if __name__ == '__main__':
      
    if len(sys.argv) > 1:
        if sys.argv[1] == "--scheme":           
            do_scheme()
        elif sys.argv[1] == "--validate-arguments":
            do_validate()
        else:
            usage()
    else:
        # Check that required file is there
        required_params = {}
        #requiredfile = SPLUNK_HOME + '/etc/apps/canvas_ta/bin/required.cfg'
        addon_path = os.path.dirname(os.path.abspath(__file__))
        addon_path = os.path.abspath(os.path.join(addon_path,os.pardir))
        #logging.info ("Addon Path is: %s" % addon_path)
        #requiredfile = SPLUNK_HOME + '/etc/apps/canvas_ta/local/canvas.conf'
        requiredfile = addon_path + '/local/canvas.conf'
        if not stanza_params_saved(requiredfile):            
    #if not os.path.isfile(requiredfile):
            logging.error("REQUIRED FILE MISSING: *** canvas.conf *** DOES NOT EXIST in app local directory")
            sys.exit(2) 
        else:
            required_config = ConfigParser.RawConfigParser()
            required_config.read(requiredfile)
            try:
                required_params["canvasurl"] = required_config.get('Required','canvasurl')
                required_params["rootaccountid"] = required_config.get('Required','rootaccountid')
                required_params["canvastoken"] = required_config.get('Required','canvastoken')
                required_params["per_page"] = required_config.get('Required','per_page')
                if required_params["per_page"] == '':
                    required_params["per_page"] = '1000'
                if required_params["rootaccountid"] == '':
                    required_params["rootaccountid"] = '1'
                #if required_params["merge_users"] == '':
                #    required_params["
                for key in required_params:
                    if required_params[key] == '':
                        logging.error("REQUIRED PARAMETERS EXIST, BUT EMPTY FROM *** app local/canvas.conf ***")
                        sys.exit(2)
                if not re.search('\d+',required_params["per_page"]):
                    logging.error("per_page needs to be a number")
                    sys.exit(2)
                if not re.search('\d',required_params["rootaccountid"]):
                    logging.error("rootaccountid needs to be a number")
                    sys.exit(2)            
            except ConfigParser.NoOptionError:
                logging.error("REQUIRED PARAMETERS DO NOT EXIST in *** app local/canvas.conf ***")
                sys.exit(2)
            try:
                required_params["start_time"] = required_config.get('Required','start_time')
            except ConfigParser.NoOptionError:
                required_params["start_time"] = ''
            try:
                required_params["end_time"] = required_config.get('Required','end_time')
            except ConfigParser.NoOptionError:
                required_params["end_time"] = ''
            try:
                required_params["merge_users"] = required_config.get('Required','merge_users')
                if required_params["merge_users"] == '':
                    required_params["merge_users"] = '1'
            except ConfigParser.NoOptionError:
                required_params["merge_users"] = '1'
            try:
                required_params["merge_logins"] = required_config.get('Required','merge_logins')
                if required_params["merge_logins"] == '':
                    required_params["merge_logins"] = '1'
            except ConfigParser.NoOptionError:
                required_params["merge_logins"] = '1'
            try:
                required_params["merge_accts"] = required_config.get('Required','merge_accts')
                if required_params["merge_accts"] == '':
                    required_params["merge_accts"] = '0'
            except ConfigParser.NoOptionError:
                required_params["merge_accts"] = '0'
            try:
                required_params["merge_pageviews"] = required_config.get('Required','merge_pageviews')
                if required_params["merge_pageviews"] == '':
                    required_params["merge_pageviews"] = '0'
            except ConfigParser.NoOptionError:
                required_params["merge_pageviews"] = '0'
            
                
#        endpoints = {'auth_logs': 'https://$canvasurl$/api/v1/audit/authentication/accounts/$rootaccountid$', 'users_lookup': 'https://$canvasurl$/api/v1/accounts/$rootaccountid$/users'}    
        endpoints = {'auth_logs': 'https://$canvasurl$/api/v1/audit/authentication/accounts/$rootaccountid$'}    
        config = get_input_config()
        STANZA = config.get("name")
        #original_endpoint=config.get("endpoint")
        try:
            original_endpoint=endpoints[STANZA[9:]]
        except KeyError:
            logging.error("Stanza %s is not a supported stanza. Only auth_logs is supported today." % STANZA[9:])
            sys.exit(2)
        #logging.info("Original Endpoint: %s" % original_endpoint)        
        #token replacement
        endpoint_list = replaceTokens(original_endpoint,required_params)
        
        sequential_mode=int(config.get("sequential_mode",0))
           
        if bool(sequential_mode):
            do_run(config,endpoint_list,required_params)
            #logging.info("do run finished")        
        else:  #parallel mode           
            for endpoint in endpoint_list:
                requester = threading.Thread(target=do_run, args=(config,[endpoint],required_params))
                requester.start()
        
    sys.exit(0)
