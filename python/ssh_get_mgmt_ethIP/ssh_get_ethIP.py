import paramiko
import getpass
import time
import socket
import re
import csv

####user credentials variable input####
username = input("What is your username?: ")
password = getpass.getpass()
fileNameRead = input("What is the filename of IP addesses?: ")
fileNameOutput = input("What should be an output filename?: ")
csvFileName = fileNameOutput.split('.')[0] 
fileNameCSV = (f"{csvFileName}.csv")
command = "ifconfig eth0 | grep \"inet \""
mgmt_ip_result = {}

####Save output to a file####
def save_to_file(content, filename):
    with open(filename, 'a') as file:
        file.write(content + '\n\n' + "##########" + '\n\n')

####regex to fetch IP address from ifconfig inet line####
def parse_ip_from_result(result_dict):
    parsed_ips = {}
    for hostname, value in result_dict.items():
        match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', value)
        if match:
            ip_address = match.group(1)  
            parsed_ips[hostname] = ip_address
    return parsed_ips


####Connect with SSH client, get output and return dictionary with mgmt IP####
def ssh_connect(ip_list, username, password, command, port=22, timeout=5):
  
    for ip in ip_list:
        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(ip, port=port, username=username, password=password, timeout=timeout)
            stdin, stdout, stderr = ssh_client.exec_command('hostname')
            hostname = stdout.read().decode('utf-8').strip()
            print("Connected to", hostname, " with Versa Private IP ", ip)
            stdin, stdout, stderr = ssh_client.exec_command(command)
            command_output = stdout.read().decode('utf-8').strip()
            if command_output:
                output_message = f"Output for {hostname} ({ip}):\n{command_output}"
                mgmt_ip_result[hostname] = command_output
            else:
                output_message = f"Output for {ip} - {hostname}:\nNO eth0 management IP conifgured"

            save_to_file(output_message, fileNameOutput)

            time.sleep(2)

            # Close the connection
            ssh_client.close()
            print(f"Disconnected from {hostname} {ip}\n")
        except paramiko.AuthenticationException:
            output_message = output_message = f"Authentication failed when connecting to {ip}\n"
            print(output_message)
            save_to_file(output_message, fileNameOutput)
        except paramiko.SSHException as sshException:
            output_message = f"Could not connect to {ip}: {sshException}\n"
            print(output_message)
            save_to_file(output_message, fileNameOutput)
        except socket.timeout:
            output_message = f"Connection to {ip} timed out.\n"
            print(output_message)
            save_to_file(output_message, fileNameOutput)
        except TimeoutError:
            output_message = f"Timed out while trying to connect to {ip}.\n"
            print(output_message)
            save_to_file(output_message, fileNameOutput)
        except Exception as e:
            print("Exception:", e)
    return mgmt_ip_result


####Save hostname and eth0 mgmt IP to csv#####
def save_to_csv(mgmt_ip_result, fileNameCSV):
    mgmt_ip_result_clean = parse_ip_from_result(mgmt_ip_result)
    with open(fileNameCSV, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Hostname', 'Versa eth0 mgmt IP Address'])
        for hostname, ip_address in mgmt_ip_result_clean.items():
            writer.writerow([hostname, ip_address])
    print(f"\n CSV File {fileNameCSV} successfully created")

        
#read file of IP addresses to which we should connect
IP_List = []
def readFromFile(fileNameRead):
    with open(fileNameRead, 'r') as file:
        # Read each line and strip any leading/trailing whitespace
        lines_list = [line.strip() for line in file]
    return lines_list


allVersa_mgmtIPs = readFromFile(fileNameRead)
mgmt_ip_result = ssh_connect(allVersa_mgmtIPs, username, password, command)
save_to_csv(mgmt_ip_result, fileNameCSV)