import argparse
import requests
import ipaddress
import socket
import pandas as pd

parser = argparse.ArgumentParser(description="get domain ip address v0.1", epilog="")
parser.add_argument("-f", "--file",   required=True, help="domain list file")
parser.add_argument("-o", "--output", default=None, help="output file")
parser.add_argument("-p", "--print", help="print", action="store_true")
args = parser.parse_args()
userFile = args.file
outFile  = args.output
printTable = args.print

def checkOptions():
    if not args.file:
        print("[-] This tool expects a domain list file, but you missed the '-f' flag.")
        exit()
    if not args.output:
        if not args.print:
            print("[-] This tool expects flags either '-o' or  '-p' but you missed both.")
            exit()
    
def getDomains(path):
    with open(path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def convertDomainToAddress(domain):
    try:
        return socket.gethostbyname(domain)
    except socket.gaierror:
        return None

def getCloudPrifixes():
    aws = requests.get("https://ip-ranges.amazonaws.com/ip-ranges.json").json()['prefixes']
    gcp = requests.get("https://www.gstatic.com/ipranges/cloud.json").json()['prefixes']
    return aws, gcp

def checkIsCloud(ip, aws_prefixes, gcp_prefixes):
    if not ip:
        return "Unresolved"
    addr = ipaddress.ip_address(ip)
    for p in aws_prefixes:
        if addr in ipaddress.ip_network(p['ip_prefix']):
            return f"Amazon Web Service"
    for p in gcp_prefixes:
        if 'ipv4Prefix' in p and addr in ipaddress.ip_network(p['ipv4Prefix']):
            return f"Google Cloud Platform"
    return ""

def putResults(domains, awsPrifixes, gcpPrifixes):
    rows = []
    for dom in domains:
        ip    = convertDomainToAddress(dom)
        cloud = checkIsCloud(ip, awsPrifixes, gcpPrifixes)
        rows.append({
            "도메인": dom,
            "IP":      ip or " ",
            "비고":    cloud
        })
    df = pd.DataFrame(rows)
    if printTable:
        print(df.to_string(index=False))
        return
    
    ext = outFile.lower()
    if ext.endswith('.xlsx'):
        df.to_excel(outFile, index=False)
    elif ext.endswith('.txt'):
        df.to_csv(outFile, sep='\t', index=False)
    else:
        print("[-] output file extension must be .xlsx or .txt")
        exit()


def main():
    checkOptions()
    domains = getDomains(userFile)
    awsPrifixes, gcpPrifixes = getCloudPrifixes()
    putResults(domains, awsPrifixes, gcpPrifixes)
    print(f'[+] Success converting Domain to Address')
    
    if outFile:
        print(f'[+] output file : {outFile}')
if __name__ == '__main__':
    main()
