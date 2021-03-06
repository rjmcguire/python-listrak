#import xml.etree.ElementTree as et
from pprint import pprint
from collections import OrderedDict
import socket, re
from datetime import datetime, timedelta
import xmltodict
import requests
from exceptions import *


class ListrakClient():
    debug = False

    def __init__(self, username, password):
        self.soap_header = """<?xml version="1.0" encoding="utf-8"?>
            <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
              <soap:Header>
                <WSUser xmlns="http://webservices.listrak.com/v31/">
                  <UserName>%s</UserName>
                  <Password>%s</Password>
                </WSUser>
              </soap:Header>
              <soap:Body>
                [BODY]
              </soap:Body>
            </soap:Envelope>""" % (username, password)

    def do_action(self, action, params=None):
        url = 'https://webservices.listrak.com/v31/IntegrationService.asmx'

        headers = {
            'SOAPAction': 'http://webservices.listrak.com/v31/%s' % action,
            'Content-Type': 'text/xml; charset=utf-8'
        }

        data = self.soap_header
        if params:
            body = '<%s xmlns="http://webservices.listrak.com/v31/">' % action
            for k,v in params.items():
                if type(v) == list:
                    for i in v:
                        body += "<%s>%s</%s>" % (k, i, k)
                else:
                    body += "<%s>%s</%s>" % (k, v, k)
            body += '</%s>' % action
            data = data.replace('[BODY]', body)
        else:
            data = data.replace('[BODY]', '<%s xmlns="http://webservices.listrak.com/v31/" />' % action)

        if self.debug:
            print data
            #return data

        response = requests.post(url, data=data, headers=headers)
        print response.text.replace(">", ">\n")
        if "[InvalidLogonAttempt]" in response.text:
            raise InvalidLogonAttempt("Invalid user name or password")
        if "[LoginAttemptsExceeded]" in response.text:
            raise InvalidLogonAttempt("Login attempts exceeded")
        if "[ProhibitedIPAddress]" in response.text:
            raise InvalidLogonAttempt(
                "IP address not allowed.  You need to add %s to your approved list." % socket.gethostbyaddr("traklis.com")[2][0])
        # Handle nil response with empty list
        #if '<WSException xsi:nil="true" />' in response.text: return [];

        results = xmltodict.parse(response.text)
        try:
            ret = results['soap:Envelope']['soap:Body']['%sResponse'%action]['%sResult'%action].items()[0][1]
        except AttributeError:
            # Single value response, no need to build a response list
            return results['soap:Envelope']['soap:Body']['%sResponse'%action]['%sResult'%action]
        except KeyError:
            return []
        # If single record returned, make it a list of 1 dict
        if type(ret) == OrderedDict:
            ret = [ret]
        for i in ret:
            for k,v in i.items():
                #if type(v) != "<type 'unicode'>":
                #    i.pop(k, None)
                if "Date" in k:
                    #print v
                    i[k] = datetime.strptime(re.sub('\.\d{1,3}','',v), "%Y-%m-%dT%H:%M:%S")
        return ret

    def get_contact(self, list_id, email):
        result = self.do_action('GetContact', {'ListID': list_id, 'ContactEmailAddress': email})
        return result

    def get_lists(self):
        lists = []
        results = self.do_action('GetContactListCollection')
        # Assign list size values
        for list in results:
            list = dict(list)
            size = self.do_action('GetFilteredListCount', {'ListID': list['ListID']})
            list['ListSize'] = size
            lists.append(list)
        return lists

    def get_list_attributes(self, list_id):
        attrs = {}
        r = self.do_action('GetProfileHeaderCollection', {'ListID': list_id})
        for attr_set in r[1:]:
            if 'Signup' in attr_set:
                print attr_set
                break
            for rr in attr_set['WSProfileAttributes']:
                try:
                    d = dict(rr)
                    attrs[d['Name']] = d
                except ValueError:
                    continue
        return attrs

    def get_saved_messages(self, list_id):
        r = self.do_action('GetSavedMessageCollection', {'ListID': list_id})
        return r

    def get_message_activity(self, list_id, days=30):
        start = (datetime.today() - timedelta(days=days)).strftime("%Y-%m-%d")
        end = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        data = {'ListID': list_id, 'StartDate':start, 'EndDate':end}
        r = self.do_action('ReportListMessageActivity', data)
        return r

    def get_list_activity(self, list_id):
        data = {'ListID': list_id, 'IncludeTerminated': '1'}
        ret = self.do_action('ReportListConversationActivity', data)
        return ret

    def get_conversations(self, list_id):
        data = {'listID': list_id}
        return self.do_action('ConductorGetConversations', data)

    def get_conversation_activity(self, list_id, convo_id, page=1, days=90):
        start = (datetime.today() - timedelta(days=days)).strftime("%Y-%m-%d")
        end = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")        
        data = {'ConversationID': convo_id, 'Page': page, 'StartDate': start, 'EndDate': end}
        return self.do_action('ReportConversationContactDelivery', data)

    def get_contact_activity(self, list_id, email, page=1):
        data = {'ListID': list_id, 'EmailAddress': email, 'Page': page}
        ret = self.do_action('ReportContactMessageActivity', data)
        return ret

    def get_msg_contact_activity(self, msg_id, page=1):
        data = {'MsgID': msg_id, 'Page': page}
        try:
            ret = self.do_action('ReportMessageContactActivity', data)
        except AttributeError:
            ret = []
        return ret

    def get_msg_opens(self, msg_id, page=1):
        data = {'MsgID': msg_id, 'Page': page}
        ret = self.do_action('ReportMessageContactOpen', data)
        return ret

    def get_msg_clicks(self, msg_id, page=1, days=30):
        start = (datetime.today() - timedelta(days=days)).strftime("%Y-%m-%d")
        end = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")        

        data = {'MsgID': msg_id, 'Page': page, 'StartDate':start, 'EndDate':end}
        ret = self.do_action('ReportRangeMessageContactClick', data)
        return ret

    def get_msg_unsubs(self, msg_id, page=1):
        data = {'MsgID': msg_id, 'Page': page}
        ret = self.do_action('ReportMessageContactRemoval', data)
        return ret

    def get_contacts_for_list(self, list_id, page=1):
        data = {'ListID': list_id, 'Page': page}
        ret = self.do_action('ReportSubscribedContacts', data)
        return ret

    def subscribe_contact(self, list_id, email, override_unsub=False):
        data = {'ListID': list_id, 'ContactEmailAddress': email, 'OverrideUnsubscribe': int(override_unsub)}
        ret = self.do_action('SubscribeContact', data)
        return ret

    def update_contact(self, list_id, email, attributes, events=''):
        xml = '<EmailAddress>%s</EmailAddress><ListID>%s</ListID>' % (email, list_id)
        data = {}
        for k, v in attributes.items():
            xml += '<ContactProfileAttribute><AttributeID>%s</AttributeID>' % k
            xml += '<Value>%s</Value></ContactProfileAttribute>' % v
        data['WSContact'] = xml
        data['ProfileUpdateType'] = 'Update'
        data['ExternalEventIDs'] = events
        data['OverrideUnsubscribe'] = 0
        ret = self.do_action('SetContact', data)
        return ret

    def upload_contacts(self):
        #TODO
        pass

    def validate(self):
        try:
            self.get_lists()
            return True
        except Exception, e:
            return e
