import pan.xapi
import xmltodict
import json
import csv
import argparse

from panos.firewall import Firewall

def send_email(output):
    import smtplib
    sender = "DEFINE_SENDING_ADDRESS"
    receivers = ['RECEIVERS']
    smtp_gw = "SMTPGW"

    message = """From: YOUR-FRIENDLY-PYTHON_SCRIPT <{}>
            Subject: LSVPN tunnel status

            {}""".format(sender, output)

    try:
        smtpObj = smtplib.SMTP('{}'.format(smtp_gw))
        smtpObj.sendmail(sender, receivers, message)
    except smtplib.SMTPException:
        print("Unable to send email")

def get_current_satellites(fw_object, gateway, tunnel_id):
    flow_cmd = "<show><running><tunnel><flow><tunnel-id>{}</tunnel-id></flow></tunnel></running></show>".format(tunnel_id)
    result = fw_object.op(cmd=flow_cmd, cmd_xml=False, xml=True)
    o = xmltodict.parse(result)
    try:
        tunnels = o['response']['result']['SSL-VPN']['entry']['users']['entry']
    except TypeError:
        return "No tunnels on gateway {}".format(gateway)
    except KeyError:
        return "Check your tunnel ID."

    xml_cmd = "<show><global-protect-gateway><current-satellite><gateway>{}</gateway></current-satellite></global-protect-gateway></show>".format(gateway)
    result = fw_object.op(cmd=xml_cmd, cmd_xml=False, xml=True)
    to_json = xmltodict.parse(result)
    sat_data = to_json['response']['result']['entry']

    output = ""
    output += "\nSatellites registered: {}\n".format(len(sat_data))
    output += "\n**********************************************************\n"

    down = 0

    filter_tunnel = {}
    for tunnel in tunnels:
        remote_ip = tunnel['remote-ip']
        context = tunnel['context']
        assigned_ip = tunnel['assigned-ip']

        if remote_ip in filter_tunnel:
            if filter_tunnel[remote_ip] != context:
                multiple = 0
                for sat in sat_data:
                    if sat['public-ip'] == remote_ip:
                        multiple += 1

                if multiple == 1:
                    print("Different context on {} ({} compared to {}). Assigned IP: {}".format(remote_ip, filter_tunnel[remote_ip], context, assigned_ip))
                    down += 1
                    output += "{}: Contexts {} and {}. Assigned IP: {}\n".format(remote_ip, filter_tunnel[remote_ip], context, assigned_ip)
                    filter_tunnel[remote_ip] = tunnel['context']
                    for sat in sat_data:
                        if sat['public-ip'] == remote_ip:
                            output += "Hostname: {}\n".format(sat['hostname'])
                            output += "Public IP: {}\n".format(sat['public-ip'])
                            output += "Tunnel IP: {}\n".format(sat['virtual-ip'])
                            output += "Login time: {}\n".format(sat['login-time-utc'])
                            output += "Tunnel monitor: {}\n".format(sat['tunnel-monitor-status'])
                            output += "Serial: {}\n".format(sat['username'])
                            output += "\n**********************************************************\n"
        else:
            filter_tunnel[remote_ip] = tunnel['context']
    output += "Total number of down tunnels: {}\n".format(down)

    return output

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-gw', required=True, help='Gateway to print info about')
    parser.add_argument('-tid', required=True, help='Tunnel ID for GW')
    parser.add_argument('-fw_ip', help='IP address of the firewall')
    parser.add_argument('-email', action="store_true", default=False, help='Set to true if you want an email report')

    args = parser.parse_args()

    gateway = args.gw
    tunnel_id = args.tid

    api_token = "YOUR_API_KEY"

    if args.fw_ip:
        host = args.fw_ip
    else:
        host = "DEFAULT_FW_IP"

    try:
        fw = Firewall(hostname=host, api_key=api_token)
    except pan.xapi.PanXapiError as msg:
        print("ERROR with the firewall connection: {}".format(msg))
        return False

    output = get_current_satellites(fw, gateway, tunnel_id)
    print(output)

    if args.email:
        send_email(output)

if __name__=="__main__":
    main()
