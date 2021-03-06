python-listrak
==============

Python wrapper for Listrak v31 SOAP API

Installation
------------
Requirements: requests, xmltodict

TODO: register with PyPI

Usage
-----
```python
from listrak import ListrakClient

client = ListrakClient('username', 'password')

lists = client.get_lists()

for l in lists:
    print "%s - %s" % (l['ListId'], l['ListName'])

# Subscribe a contact
list_id = lists[0]['ListId']
client.subscribe_contact(list_id, 'somenewemail@abc.com')

# Update a segmentation attribute
some_attr_id = client.get_list_attributes(list_id)['some_attr']['AttributeID']
client.update_contact(list_id, 'somenewemail@abc.com', {some_attr_id: 'NEW VALUE'})
```

Methods
-------
* get_conversations(list_id)
* get_conversation_activity(convo_id, page, days)
* get_contact_activity(list_id, email, page)
* get_lists()
* get_list_attributes(list_id)
* get_saved_messages(list_id)
* get_message_activity(list_id)
* get_message_opens(msg_id)
* get_msg_clicks(msg_id)
* get_msg_unsubs(msg_id)
* validate() # For user/pass and ip access validation
* subscribe_contact(list_id, email)
* update_contact(list_id, email, attribute_dict)
* upload_contacts() # TODO


Version History
---------------
* 0.9 - added conversation related calls
* 0.8 - added externaleventid param to update_contact to allow events to trigger conducter
* 0.7 - update_contact, get_list_attributes, subscribe_contact added.  Fixed bug in response when 1 item is returned
* 0.6 - get_list_attributes and update_contact methods added
* 0.5 - get_msg methods
* 0.4 - Custom exception handling, user/pass validation, auto datetime conversion
* 0.3 - New message methods, added param passing to SOAP request
* 0.2 - SOAP requests working.  get_lists() added as first method
* 0.1 - First commit
