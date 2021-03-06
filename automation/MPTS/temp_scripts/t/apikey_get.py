import json
import requests
import md5
import fileinput
import subprocess
import time
import datetime

#NoofAccounts=_MyValue_
#NoofTSMs=_MyValue_
#NoofNFSVolumes=_MyValue_
#NoofISCSIVolumes=_MyValue_

#### Function(s) Declaration Beginso
def executeCmd(command):
    #print command
    link = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    ldata = link.stdout.readlines()
    output, errors = link.communicate()
    rco = link.returncode
    if rco != 0:
       return "FAILED", str(errors)
    return "PASSED", "";

def sendrequest(url, querystring): 
    #print url+querystring
    response = requests.get(
      stdurl+querystring, verify=False
    )   
    return(response);

def filesave(loglocation,permission,content):
    f=open(loglocation,permission) 
    f.write(content.text)
    f.close()
    return;

def timetrack(event):
    f=open("results/config_creation_result.csv","a")
    f.write(event)
    f.write("--")
    time = datetime.datetime.now()
    f.write(str(time))
    f.write("\n")
    f.close()
    return;

#### Function(s) Declartion Ends


config = {}
with open('config.txt') as cfg:
  config = json.load(cfg)

#######Generate Apikeys
m = md5.new()
m.update("%s" %(config['admin_org_password']))
md5_org_pwd =  m.hexdigest()
m = md5.new()
m.update("%s" %(config['admin_set_password']))
md5_set_pwd =  m.hexdigest()
stdurl_noapikey = 'https://%s/client/api?response=%s&' %(config['host'], config['response'])

s = requests.session()
payload = {'command': 'login', 'username': 'admin', 'password': md5_set_pwd, 'domain': '/', 'response': 'json'}

### First time login
r = s.post(stdurl_noapikey, verify=False, data=payload)


### List userid
querystring = 'command=listUsers'
r = s.get(stdurl_noapikey+querystring, verify=False)
data = json.loads(r.text)
users = data["listusersresponse"]["user"]
for user in users:
    if user['username'] == "admin":
        user_id = user['id']
        apikey = user['apikey']

#print apikey
'''
### Update User ID
querystring = 'command=updateUser&id=%s&password=%s&firstname=%s&lastname=%s&email=%s&mobileno=%s' %(user_id, md5_set_pwd, config['firstname'], config['lastname'], config['email'], config['mobile'])
r = s.get(stdurl_noapikey+querystring, verify=False)

### Update Email ID
querystring = 'command=updateConfiguration&name=alert.email.addresses&value=%s' %(config['email'])
r = s.get(stdurl_noapikey+querystring, verify=False)
'''
apikey1 = config['apikey']
#print apikey1
### Generate ApiKey
querystring = 'command=registerUserKeys&id=%s' %(user_id)
r = s.get(stdurl_noapikey+querystring, verify=False)
data = json.loads(r.text)
apikey2 = data["registeruserkeysresponse"]["userkeys"]["apikey"]
#print apikey2
cmd1="'s/%s/%s/g' config.txt" %(apikey1,apikey2)
cmd="sed -i %s" %(cmd1)
res = executeCmd(cmd)
if res[0] == "PASSED" :
    print "apikey is Copied to config.txt"
cfg.close()
#############Apikey Generated
