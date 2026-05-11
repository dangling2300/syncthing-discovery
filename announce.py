#!/usr/bin/env python3


import requests
import json
import tempfile
import sys
import os
import time

obj = json.load(open("test.json","r"))


def announce_to_discovery(
    discovery_url="https://discovery.syncthing.net/",
    addresses=["udp://1.1.1.1:123"],

):
    """
    Announce addresses to a Syncthing discovery server

    Args:
        discovery_url: URL of the discovery server
        cert_file: Path to certificate file
        key_file: Path to key file
        addresses: List of addresses in format "tcp://ip:port"
                  (Use format tcp://:port to let server use the request's source IP)
        legacy: If True, appends /v2/ to the URL for compatibility with older Syncthing (pre-v0.14.44)

    Returns:
        (success, wait_time): Tuple with success status and wait time before next announcement
    """
    # Handle URL path for legacy mode
    
    discovery_url = f"{discovery_url}/v2/"

    # Prepare JSON payload
    payload = {"addresses": addresses}

    if True:
        print(f"Announcing to {discovery_url} with addresses: {addresses}")
        url="https://discovery.syncthing.net/v2/?device="+obj["deviceID"]
        response = requests.get(url,verify=False)
        print(response.text)
        print(url)
        cert_file=tempfile.NamedTemporaryFile(mode='w',delete=False) 
        key_file =tempfile.NamedTemporaryFile(mode='w',delete=False)
        cert_file.write(obj["cert"])
        key_file.write(obj["key"])
        cert_file.flush()
        key_file.flush()
        cert_file.close()
        key_file.close()
        # Make HTTPS POST request with client certificate
        response = requests.post(
            discovery_url, json=payload, cert=(cert_file.name, key_file.name), verify=False
        )
      

        # Process response
        if response.status_code == 204:
            reannounce_after = response.headers.get("Reannounce-After", "300")
            print(
                f"Announcement successful. Reannounce after {reannounce_after} seconds."
            )
            return True, int(reannounce_after) if reannounce_after.isdigit() else 300
        elif response.status_code == 403:
            print("Error: Certificate authentication failed (403 Forbidden)")
        elif response.status_code == 400:
            print("Error: Bad request - invalid payload format (400 Bad Request)")
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "60")
            print(
                f"Error: Too many requests. Retry after {retry_after} seconds. (429 Too Many Requests)"
            )
            return False, int(retry_after) if retry_after.isdigit() else 60
        else:
            print(
                f"Error: Unexpected response - {response.status_code}: {response.text}"
            )

        return False, 0


def main():
    if True:
        
        try:
            while True:
                success, wait_time = announce_to_discovery()

                wait_time = max(
                    wait_time, 60
                )  # Wait at least 60 seconds between attempts
                print(f"Waiting {wait_time} seconds before next announcement...")
                time.sleep(wait_time)

        except KeyboardInterrupt:
            print("\nStopping announcement service.")
            sys.exit(0)



if __name__ == "__main__":
    main()
