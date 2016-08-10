#add your custom response handler class to this module
import json
import datetime
import logging
import requests
import time
import sys
import csv
import os


class CanvasAuthLogHandler:

    def __init__(self,**args):
        pass
        
    def __call__(self, response_object,raw_response_output,response_type,req_args,endpoint,options):
        backoff_time = 10
        usersd = {}
        loginsd = {}
        acctsd = {}
        pagevsd = {}
        
        #logging.info(req_args)
        
        starttime = req_args["params"]["start_time"]
        endtime = req_args["params"]["end_time"]
        if starttime == '' or endtime == '':
            logging.error("Start Time or End Time is Missing - Cannot Load Data into Splunk.")
            return
        #    
        req_args["params"]["start_time"] = endtime
        req_args["params"]["end_time"] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")                          
        header=response_object.request.headers
        if response_type == "json":      
            output = json.loads(raw_response_output)
            if options["mergeUsers"] == '1':
                for user in output["linked"]["users"]:
                    uid = user["id"]
                    usersd[uid]={}
                    usersd[uid]=user
            if options["mergeLogins"] == '1':
                for login in output["linked"]["logins"]:
                    lid = login["id"]
                    loginsd[lid]={}
                    loginsd[lid]=login
            if options["mergeAccts"] == '1':
                for account in output["linked"]["accounts"]:
                    aid = account["id"]
                    acctsd[aid]={}
                    acctsd[aid]=account
            if options["mergePageViews"] == '1':
                for page_view in output["linked"]["page_views"]:
                    pid = page_view["id"]
                    pagevsd[pid]={}
                    pagevsd[pid]=page_view
            for event in output["events"]:
                #users["users"] = usersd[event["links"]["user"]]
                #logins["logins"] = loginsd[event["links"]["login"]]
                #accounts
                if options["mergeUsers"] == '1':
                    event["user"]={}
                    for key in usersd[event["links"]["user"]]:
                        event["user"][key] = usersd[event["links"]["user"]][key]
                if options["mergeLogins"] == '1':
                    event["login"]={}
                    for key in loginsd[event["links"]["login"]]:
                        event["login"][key] = loginsd[event["links"]["login"]][key]
                if options["mergeAccts"] == '1':
                    event["account"]={}
                    for key in acctsd[event["links"]["account"]]:
                        event["account"][key] = acctsd[event["links"]["account"]][key]
                if options["mergePageViews"] == '1':
                    event["page_view"]={}
                    try:
                        for key in pagevsd[event["links"]["page_view"]]:
                            event["page_view"][key] = pagevsd[event["links"]["page_view"]][key]
                    except KeyError:
                        del event["page_view"]
                print_xml_stream(json.dumps(event))
                #print_xml_stream(json.dumps(event) + ',' + json.dumps(users) + ',' + json.dumps(logins))
                #print_xml_stream(json.dumps(event + users + logins))
                #print_xml_stream(json.dumps(event))
                #print_xml_stream(json.dumps(users))
                #print_xml_stream(json.dumps(logins))
        #follow any pagination links in the response
            try:
                next_link = response_object.links["next"]
                while next_link:
                    try:
                        next_response = requests.get(next_link["url"],headers=header)
                    except requests.exceptions.Timeout,e:
                        logging.error("HTTP Request Timeout error: %s" % str(e))
                        time.sleep(float(backoff_time))
                        continue
                    except Exception as e:
                        logging.error("Exception performing request: %s" % str(e))
                        time.sleep(float(backoff_time))
                        continue
                    try:
#                        logging.info("Request Text: %s" % next_response.text)
#                        logging.info("Response Headers: %s" % next_response.headers)
#                        logging.info("Before raise for status")
                        next_response.raise_for_status()
                        output = json.loads(next_response.text)
                        if options["mergeUsers"] == '1':
                            for user in output["linked"]["users"]:
                                uid = user["id"]
                                usersd[uid]={}
                                usersd[uid]=user
                        if options["mergeLogins"] == '1':
                            for login in output["linked"]["logins"]:
                                lid = login["id"]
                                loginsd[lid]={}
                                loginsd[lid]=login
                        if options["mergeAccts"] == '1':
                            for account in output["linked"]["accounts"]:
                                aid = account["id"]
                                acctsd[aid]={}
                                acctsd[aid]=account
                        if options["mergePageViews"] == '1':
                            for page_view in output["linked"]["page_views"]:
                                pid = page_view["id"]
                                pagevsd[pid]={}
                                pagevsd[pid]=page_view
                        for event in output["events"]:
                            #users["users"] = usersd[event["links"]["user"]]
                            #logins["logins"] = loginsd[event["links"]["login"]]
                            if options["mergeUsers"] == '1':
                                event["user"]={}
                                for key in usersd[event["links"]["user"]]:                           
                                    event["user"][key] = usersd[event["links"]["user"]][key]
                            if options["mergeLogins"] == '1':
                                event["login"]={}
                                for key in loginsd[event["links"]["login"]]:   
                                    event["login"][key] = loginsd[event["links"]["login"]][key]
                            if options["mergeAccts"] == '1':
                                event["account"]={}
                                for key in acctsd[event["links"]["account"]]:
                                    event["account"][key] = acctsd[event["links"]["account"]][key]
                            if options["mergePageViews"] == '1':
                                event["page_view"]={}
                                try:
                                    for key in pagevsd[event["links"]["page_view"]]:
                                        event["page_view"][key] = pagevsd[event["links"]["page_view"]][key]
                                except KeyError:
                                    del event["page_view"]
                            #print_xml_stream(json.dumps(event) + ',' + json.dumps(users) + ',' + json.dumps(logins))
                            #print_xml_stream(json.dumps(event + users + logins))
                            print_xml_stream(json.dumps(event))
                            #print_xml_stream(json.dumps(logins))
                        next_link = next_response.links["next"]                            
                    except requests.exceptions.HTTPError,e:
                        error_output = next_response.text
                        error_http_code = next_response.status_code
                        #if index_error_response_codes:
                        #    error_event=""
                        #    error_event += 'http_error_code = %s error_message = %s' % (error_http_code, error_output) 
                        #    print_xml_single_instance_mode(error_event)
                        #    sys.stdout.flush()
                        logging.error("HTTP Request error: %s" % str(e))
                        time.sleep(float(backoff_time))
                        continue
            except KeyError:
                pass
                                                                                         
#HELPER FUNCTIONS
    
# prints XML stream
def print_xml_stream(s):
    print "<stream><event unbroken=\"1\"><data>%s</data><done/></event></stream>" % encodeXMLText(s)



def encodeXMLText(text):
    text = text.replace("&", "&amp;")
    text = text.replace("\"", "&quot;")
    text = text.replace("'", "&apos;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace("\n", "")
    return text