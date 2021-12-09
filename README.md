# PAN-IPSEC-rekey
Troubleshooting scripts for Palo Alto issues.

Usage:
```
python3 main.py
usage: main.py [-h] -gw GW -tid TID [-fw_ip FW_IP] [-email]
```

Find the tunnel id for your gateway by running `show running tunnel flow`.

Required attributes that need defining is:  
Your API Key - replace YOUR_API_KEY with the API key with access to the firewall.

Optional if you want to send email reports:  
Sender address - replace DEFINE_SENDING_ADDRESS  
Receivers - replace RECEIVERS (can be a list)  
SMTP gw - replace SMTPGW  
