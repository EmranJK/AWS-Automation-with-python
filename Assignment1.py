#!/usr/bin/env python3

import boto3
import subprocess
import webbrowser
import time

############################### *********************** #######################################

# THE FOLLOWING ARE THE VARIABLES THAT YOU WILL NEED TO CHANGE THEIR VALUES IF YOU DON'T WANT TO USE THE DEFAULT VALUES.
# THEY ARE GLOBAL VARIABLES USED BY FUNCTIONS, SO THIS IS THE ONLY PLACE WHERE YOU HAVE TO CHANGE THEM.
# THIS TECHNIQUE WILL PREVENT THE USER FROM INPUTTING VALUES OR USING COMMAND ARGUMENTS EVERY TIME HE/SHE WANTS TO LAUNCH THE CODE.

instance_keyname = 'emran2' # CHANGE THIS TO YOUR KEY, DON'T INCLUDE THE .pem EXTENTION
instance_security_groups = ['httpssh2'] # CHANGE THIS TO YOUR SECURITY GROUP
bucket_name = 'emran-bucket1-2021-10-18-1483305884' # CHANGE THIS TO YOUR BUCKET NAME

############################### *********************** #######################################

instance_ID = '' # DON'T TOUCH THIS

print('''
!!! IMPORTANT NOTE: THE VALUES OF THE VARIABLES instance_keyname, instance_security_groups AND bucket_name ARE HARDCODED,
TO CHANGE THEIR VALUES PLEASE FOLLOW THE FOLLOWING STEPS:

1) OPEN THE SCRIPT WITH A NOTEPAD OR SIMILAR.
2) CHANGE THE VALUES OF THE MENTIONED VARIABLES TO ANY VALUES YOU PREFER, THE VARIABLES CAN BE FOUND JUST UNDER THE IMPORTS.
3) SAVE THE CHANGES AND RUN THE SCRIPT.

This script is designed to automate the following: 
-Creating an ec2 instance
-Creating a local server and host simple html content
-Creating an s3 bucket
-Putting simple html content as objects in the bucket
-Configuring a static website for the s3 bucket
-Launching a browser an navigating to the ec2 instance local web server page and the s3 bucket static website
-Monitoring the instance
''')



def create_instance():

	# THE FOLLOWING FUNCTION WILL CREATE AND RUN AND INSTANCE
	# THE USER DATA PARAMETER WILL INSTALL HTTPD, MARIADB AND INSERT DATA IN MARIADB
	# TAGS, KEYNAME, SECURITY GROUPS, INSTANCE TYPES ARE ALL CONFIGURED
	# KEYNAME AND SECURITY GROUPS USE GLOBAL VARIABLES TO MAKE THE VALUE CHANGE EASIER FOR THE USER,
	# THIS WILL ALLOW THE USER TO CHANGE THE VALUES OF THE MENTIONED PARAMETERS ONCE AND FROM ONE PLACE
	# WAITERS ARE USED TO INFORM THE USER ONCE THE INSTANCE STARTS RUNNING

	ec2 = boto3.resource('ec2')
	new_instance = ec2.create_instances(
	ImageId='ami-0d1bf5b68307103c2',
	MinCount=1,
	MaxCount=1,
	UserData='''
	#!/bin/bash
	sudo yum install httpd -y
	sudo systemctl enable httpd
	sudo systemctl start httpd
	echo '<html>' > index.html
	echo 'Private IP address: ' >> index.html
	curl http://169.254.169.254/latest/meta-data/local-ipv4 >> index.html
	cp index.html /var/www/html/index.html
	sudo yum install mariadb-server -y
	sudo systemctl enable mariadb
	sudo systemctl start mariadb
	mysql -u=root test << EOF
	CREATE TABLE IF NOT EXISTS functions (
	    task_id INT AUTO_INCREMENT,
	    title VARCHAR(255) NOT NULL,
	    start_date DATE,
	    due_date DATE,
	    priority TINYINT NOT NULL DEFAULT 3,
	    description TEXT,
	    PRIMARY KEY (task_id)
	);
	EOF
	'''
	,
	InstanceType='t2.nano',
	KeyName=instance_keyname,
	SecurityGroups = instance_security_groups,
	TagSpecifications=[
		{
		    'ResourceType': 'instance',
		    'Tags': [
		        {
		            'Key': 'Name',
		            'Value': 'My instance'
		        },
		    ]
		},
	    ]
	)
	# securitygroup = ec2.create_security_group(GroupName='SSH-ONLY', Description='only allow SSH traffic', VpcId=vpc.id)
	# securitygroup.authorize_ingress(CidrIp='0.0.0.0/0', IpProtocol='tcp', FromPort=22, ToPort=22)
	#print (new_instance[0].id)
	global instance_ID
	instance_ID = new_instance[0].id
	print('WAITING FOR THE EC2 INSTANCE TO RUN, PLEASE WAIT...')
	new_instance[0].wait_until_running()
	print('EC2 INSTANCE IS NOW RUNNING')
	print('')
	# subprocess.run('ssh -o StrictHostKeyChecking=no -i emran2.pem hello.py ec2-user@192.168.1.2')
	

def subP():

    # THIS FUNCTION WILL USE SUBPROCESS LIBRARY TO DOWNLOAD AN IMAGE FROM THE WEB USING CURL
    # THEN IT CREATES AN HTML FILE WITH AN IMAGE TAG TO HOST THIS IMAGE ON A STATIC WEBSITE LATER
    
    subprocess.run('curl -O http://devops.witdemo.net/assign1.jpg', shell=True)
    subprocess.run(""" echo "<html><body><img src='assign1.jpg' alt='image'></body></html>" > index.html """, shell=True)

#################

def create_bucket():
	
	# THIS FUNCTION WILL CREATE AN S3 BUCKET
	# IT MAKES IT PUBLICALLY READABLE AND CONFIGURES ITS REGION
	# IT ALSO CONTAINS ERROR HANDLING
	
	s3 = boto3.resource("s3")
	try:
	    response = s3.create_bucket(Bucket=bucket_name, ACL='public-read', CreateBucketConfiguration={'LocationConstraint': 'eu-west-1'})
	    print (response)
	except Exception as error:
	    print (error)

def put():
    
    # THIS METHOD WILL PUT THE IMAGE AND THE HTML FILE THAT WE MENTIONED EARLIER IN THE S3 BUCKET AS OBJECTS
    # THEN IT WILL MAKE THEM PUBLIC AND GIVE THEM AN APPROPRIATE CONTENT TYPE
    # IT ALSO CONTAINS ERROR HANDLING
    
    
    s3 = boto3.resource("s3")
    # bucket_name = 'emran-bucket1-2021-10-07-1483305884'
    object_name2 = 'assign1.jpg'
    object_name = 'index.html'
    try:
        response = s3.Object(bucket_name, object_name).put(Body=open(object_name, 'rb'), ACL='public-read', ContentType='text/html')
        print (response)
    except Exception as error:
        print (error)

    try:
        response = s3.Object(bucket_name, object_name2).put(Body=open(object_name2, 'rb'), ACL='public-read', ContentType='image/jpeg')
        print (response)
    except Exception as error:
        print (error)

def staticc():

    # THIS FUNCTION WILL CONFIGURE A STATIC WEBSITE AS FOLLOWS

    # First it defines the website configuration
    website_configuration = {
        'ErrorDocument': {'Key': 'error.html'} ,
        'IndexDocument': {'Suffix': 'index.html'},
    }

    # Then it sets the website configuration
    s3 = boto3.client('s3')
    s3.put_bucket_website(
    Bucket = bucket_name, WebsiteConfiguration=website_configuration)
    
def browser():

	# THIS FUNCTION GETS THE IP ADDRESS OF THE NEWLY CREATED INSTANCE
	# IT CHECKS FOR AN INSTANCE THAT HAS A CERTAIN ID,
	# IF THE INSTANCE HAS THAT ID THEN ITS PUBLIC IP WILL BE ADDED TO A LIST CALLED LISTY
	# IT WILL THEN GIVE THE USER SOME INFORMATION ABOUT THE STATUS OF THE INSTANCE
	# THEN IT UPLOADS THE monitor.sh SCRIPT TO THE INSTANCE WITH SCP
	# IT MAKES IT EXECUTABLE AND LAUNCHES IT AND SHOWS ITS OUTPUT TO THE USER
	listy=[]
	ec2 = boto3.resource('ec2')
	for inst in ec2.instances.all():
		if inst.id == instance_ID:
	        	listy.append(inst.public_ip_address)
	#print(listy[0])
	print('')
	print('INSTALLING HTTPD AND MARIADB ON THE EC2 INSTANCE, THIS MIGHT TAKE A MINUTE, PLEASE WAIT...')
	time.sleep(50)
	print('HTTPD INSTALLED, LAUNCHING A BROWSER')
	print('')
	print('''MARIADB IS NOW INSTALLED AND HAS DATA IN IT,
	USE THE COMMAND mysql -u root TO START USING THE DATABASE AFTER YOU LOGIN INTO THE INSTANCE WITH SSH
	CHECK THE DATABASE test FOR A TABLE CALLED functions''')
	print('')
	print('LAUNCHING monitor.sh')
	print('')
	webbrowser.open_new_tab(listy[0])
	webbrowser.open_new_tab('http://' + bucket_name + '.s3-website-eu-west-1.amazonaws.com')
	subprocess.run('scp -o StrictHostKeyChecking=no -i ' + instance_keyname+'.pem' + ' monitor.sh ec2-user@' + listy[0]+ ':.', shell=True)
	subprocess.run("ssh -o StrictHostKeyChecking=no -i " + instance_keyname+".pem" + " ec2-user@" + listy[0] + " 'chmod +x monitor.sh'", shell=True)
	subprocess.run("ssh -o StrictHostKeyChecking=no -i " + instance_keyname+".pem" + " ec2-user@" + listy[0] + " './monitor.sh'", shell=True)
		
try:
	create_instance()
	create_bucket()
	subP()
	staticc()
	put()
	browser()
except:
	print('''
	!ERROR!
	
	The program has crashed, please check the following in order to fix the problem:
	1) Check the network connection
	2) Check you spelled the name of the bucket correctly with no upper case letters
	3) Check that you didn't add the .pem extention when typing you key name and that you spelled the name correctly 
	4) Check that you are not creating the same bucket twice
	5) Check that all the required variable at the top of the script have values
	6) Check that the script, the key and the monitor.sh script are all in the same directory
	
	''')

# REFERENCES:
# https://www.youtube.com/watch?v=CBGMYq7d2NM
# https://stackoverflow.com/questions/39215064/insert-into-mysql-from-bash-script
# https://www.mysqltutorial.org/mysql-insert-statement.aspx
