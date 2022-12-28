#!/usr/bin/env python3
import json
import argparse
import subprocess
import re

#import docker_registry_list

import pdb

def get_all_images(kube_context):
    cmd = subprocess.run(["kubectl", f'--context={kube_context}',
                         "get", "pods", "--all-namespaces",
                         "--output=jsonpath='{.items[*].status.containerStatuses[*].image}'"],
                         capture_output=True, text=True, check=True)

    images = [i.replace("'", "") for i in cmd.stdout.split(' ')]

    #TODO Remove dups
    return images

def build_image_dicts(images):
    image_dicts = []

    for image in images:
        image_name = image.split(':')[0]
        tag = image.split(':')[1]

        if match := re.search("^.*\.[a-z]*$", image_name.split('/')[0]):
            registry = match[0]
            image_name = '/'.join(image_name.split('/')[1:])
        else:
            registry = 'docker.io'

        image_dict = {
            "registry": registry,
            "image_name": image_name,
            "tag": tag,
            "updates": []
        }
        
        image_dicts.append(image_dict)

    return image_dicts

def get_current_context():
    if cmd :=subprocess.run(["kubectl", "config", "current-context"], capture_output=True, text=True, check=True):
        return cmd.stdout.strip()


if __name__ == "__main__":
    p = argparse.ArgumentParser()

    p.add_argument('-k', '--kube-context',
                   help='Context for kubectl. Defaults to current-context if not set')

    args = p.parse_args()

    kube_context = args.kube_context or get_current_context()
    
    images = build_image_dicts(set(get_all_images(kube_context)))

    print(json.dumps(images))
