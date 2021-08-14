import json
import paramiko
import boto3
import os

S3Bucket = os.getenv('S3Bucket')
EC2Key = os.getenv('EC2Key')
EC2TempKey = os.getenv('EC2TempKey')
EC2Host = os.getenv('EC2Host')
SourcePath = os.getenv('SourcePath')
S3SFTPPrefix = os.getenv('S3SFTPPrefix')
FilePattern = os.getenv('FilePattern')
EC2User = os.getenv('EC2User')

def lambda_handler(event, context):
    S3Client = boto3.client('s3')
    S3Client.download_file (S3Bucket, EC2Key, EC2TempKey)
    pem_key = paramiko.RSAKey.from_private_key_file(EC2TempKey)
    
    #Create a new client
    SSHClient = paramiko.SSHClient()
    SSHClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    SSHClient.connect (hostname = EC2Host, username = EC2User, pkey = pem_key)
    print("Connected to: " + EC2Host)
    
    rawcommand = 'find {path} -name {pattern}'
    command = rawcommand.format(path = SourcePath, pattern = FilePattern)
    stdin, stdout, stderr = SSHClient.exec_command(command)
    FileList = stdout.read().splitlines()
    
    SFTPClient = SSHClient.open_sftp()
    FileCount = 0
    for TrigFile in FileList:
        (head, filename) = os.path.split(TrigFile)
        FileName = filename.decode('utf-8')
        print(FileName)
        TempFile = '/tmp/' + FileName
        S3File = S3SFTPPrefix + FileName
        SFTPClient.get(TrigFile, TempFile)
        S3Client.upload_file(TempFile, S3Bucket, S3File)
        SFTPClient.remove(TrigFile)
        FileCount += 1
    SFTPClient.close()
    SSHClient.close()
    
    return str(FileCount) + " file(s) have been uploaded to the S3 bucket."
