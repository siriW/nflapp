# nfl application

####How to run:

- pip install awscli

Configure your aws AccessKey and SecretKey using the below command

- aws configure

Enter keys and region when prompted (us)

aws cloudformation create-stack --stack-name nflapp --template-body file://cloudformation.yaml --parameters ParameterKey=KeyPairName,ParameterValue=ubuntu --region us-east-2

optionally, --region flag can be passed.

###End points:

####Ingestion:

http://<<ec2-public-ip>>:5000/ingest?season=2018&seasonType=REG

####Byeweek:
##### by team alias:
http://<<ec2-public-ip>>:5000/byeweek?season=2016&team_alias=CHI

##### by all teams: 
http://<<ec2-public-ip>>:5000/byeweek?season=2016


####Average points after byeweek:
 
http://<<ec2-public-ip>>:5000/average?season=2018&team_alias=CHI

