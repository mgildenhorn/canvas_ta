import splunk.admin as admin
import splunk.entity as en
# import your required python modules
class ConfigApp(admin.MConfigHandler):
    def setup(self):
        if self.requestedAction == admin.ACTION_EDIT:
            for arg in ['canvasurl', 'rootaccountid', 'canvastoken', 'per_page', 'start_time', 'end_time', 'merge_users', 'merge_logins','merge_accts','merge_pageviews']:
                self.supportedArgs.addOptArg(arg)
                
    def handleList(self, confInfo):
        confDict = self.readConf("canvas")
        if None != confDict:
            for stanza, settings in confDict.items():
                for key, val in settings.items():
          #if key in ['field_2_boolean']:
          #  if int(val) == 1:
          #    val = '0'
          #  else:
          #    val = '1'
          #if key in ['field_1'] and val in [None, '']:
          #  val = ''
                    if key in ['canvasurl'] and val in [None, '']:
                        val = ''
                    if key in ['canvastoken'] and val in [None, '']:
                        val = ''
                    if key in ['start_time'] and val in [None, '']:
                        val = ''
                    if key in ['end_time'] and val in [None, '']:
                        val = ''
                    if key in ['per_page'] and val in [None,'']:
                        val = '1000'
                    if key in ['rootaccountid'] and val in [None, '']:
                        val = '1' 
                    if key in ['merge_users'] and val in [None, '']:
                        val = '1' 
                    if key in ['merge_logins'] and val in [None, '']:
                        val = '1' 
                    if key in ['merge_accts'] and val in [None, '']:
                        val = '0' 
                    if key in ['merge_pageviews'] and val in [None, '']:
                        val = '0' 


                    confInfo[stanza].append(key, val)

    def handleEdit(self, confInfo):
        name = self.callerArgs.id
        args = self.callerArgs
        #if int(self.callerArgs.data['field_3'][0]) < 60:
        #    self.callerArgs.data['field_3'][0] = '60'
        #if int(self.callerArgs.data['field_2_boolean'][0]) == 1:
        #    self.callerArgs.data['field_2_boolean'][0] = '0'
        #else:
        #    self.callerArgs.data['field_2_boolean'][0] = '1'
        #if self.callerArgs.data['field_1'][0] in [None, '']:
        #    self.callerArgs.data['field_1'][0] = ''
        if self.callerArgs.data['per_page'][0] in [None, '']:
            self.callerArgs.data['per_page'][0] = '1000'
        if self.callerArgs.data['rootaccountid'][0] in [None, '']:
            self.callerArgs.data['rootaccountid'][0] = '1'
        if self.callerArgs.data['canvasurl'][0] in [None, '']:
            self.callerArgs.data['canvasurl'][0] = ''
        if self.callerArgs.data['canvastoken'][0] in [None, '']:
            self.callerArgs.data['canvastoken'][0]  = ''
        if self.callerArgs.data['start_time'][0] in [None, '']:
            self.callerArgs.data['start_time'][0] = ''
        if self.callerArgs.data['end_time'][0] in [None, '']:
            self.callerArgs.data['end_time'][0] = ''
        if self.callerArgs.data['merge_users'][0] in [None, '']:
            self.callerArgs.data['merge_users'][0] = '1'
        if self.callerArgs.data['merge_logins'][0] in [None, '']:
            self.callerArgs.data['merge_logins'][0] = '1'
        if self.callerArgs.data['merge_accts'][0] in [None, '']:
            self.callerArgs.data['merge_accts'][0] = '0'
        if self.callerArgs.data['merge_pageviews'][0] in [None, '']:
            self.callerArgs.data['merge_pageviews'][0] = '0'



        self.writeConf('canvas', 'Required', self.callerArgs.data)
# initialize the handler
admin.init(ConfigApp, admin.CONTEXT_NONE)