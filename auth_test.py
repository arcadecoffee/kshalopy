import pprint
import boto3
from kshalopy import AWSSRP

user_pool_id = 'us-east-1_6B3uo6uKN'
client_id = '5eu1cdkjp1itd1fi7b91m6g79s'
username = '******REMOVED******'
password = '******REMOVED******'

client = boto3.client('cognito-idp', region_name='us-east-1')
a = AWSSRP(username=username, password=password, user_pool_id=user_pool_id,
           client_id=client_id, device_key='foo')

auth_params = a.get_auth_params()
#auth_params.update({'DEVICE_KEY': 'foo', 'CHALLENGE_NAME': 'SRP_A'})

response_1 = client.initiate_auth(
    AuthFlow='CUSTOM_AUTH',
    AuthParameters=auth_params,
    ClientId=client_id)

challenge_responses = a.process_challenge(response_1['ChallengeParameters'])

response_2 = client.respond_to_auth_challenge(
    ChallengeName='PASSWORD_VERIFIER',
    ChallengeResponses=challenge_responses,
    ClientId=client_id,
    Session=response_1['Session'])

medium = ''
while medium not in ('email', 'phone'):
    medium = input('Medium (phone or email) [phone]: ')
    medium = 'phone' if medium == '' else ''

answer_1 = f'answerType:generateCode,medium:{medium},codeType:login'

response_3 = client.respond_to_auth_challenge(
    ChallengeName='CUSTOM_CHALLENGE',
    ChallengeResponses={'ANSWER': answer_1, 'USERNAME': username},
    ClientId=client_id,
    Session=response_2['Session'])

code = input('Code: ')
answer_2 = f'answerType:verifyCode,medium:{medium},codeType:login,code:{code}'

tokens = client.respond_to_auth_challenge(
    ChallengeName='CUSTOM_CHALLENGE',
    ChallengeResponses={'ANSWER': answer_2, 'USERNAME': username},
    ClientId=client_id,
    Session=response_3['Session'])

pprint.pprint(tokens)