#!/usr/bin/env python3
import argparse
import json
import re
import requests
import subprocess

def get_all_images(kube_context):
    cmd = subprocess.run(["kubectl", f'--context={kube_context}',
                         "get", "pods", "--all-namespaces",
                         "--output=jsonpath='{.items[*].status.containerStatuses[*].image}'"],
                         capture_output=True, text=True, check=True)

    images = [i.replace("'", "") for i in cmd.stdout.split(' ')]
    unique_images = list(dict.fromkeys(images))

    return unique_images

def get_quay_tag_list(image_name, tag):
    page = 1
    has_additional = True
    updated_tags = []

    while has_additional:
        r = requests.get('https://quay.io/api/v1/repository/{}/tag?page={}'.format(image_name, page))

        for t in r.json()['tags']:
            if tag == t['name']:
                break
            else:
                updated_tags.append(t['name'])
                
        has_additional = r.json()['has_additional']
        page += 1

    updated_tags = list(dict.fromkeys(updated_tags))
    return updated_tags

def get_docker_tag_list(image_name, tag):
    r = requests.get('https://auth.docker.io/token?service=registry.docker.io&scope=repository:{}:pull'.format(image_name))
    auth_token = r.json()['token']
    
    r = requests.get('https://index.docker.io/v2/{}/tags/list'.format(image_name),
                    headers={'Authorization': "Bearer {}".format(auth_token)})

    tags = list(dict.fromkeys(r.json()['tags']))

    try:
        index = int(tags.index(tag)) + 1
        newer_tags = tags[index:]
    except ValueError:
        print(f'Warning: {tag_list["name"]} - Cannot filter for newer tags as current tag \"{tag}\" was not found in tag list. All tags will be listed.')
        newer_tags = tags
    
    return newer_tags

    return r.json()

def build_updated_tags_lists(registry, image_name, tag):
    updated_tags = False

    match registry:
        case "docker.io":
            updated_tags = get_docker_tag_list(image_name, tag)
        case "quay.io":
            updated_tags = get_quay_tag_list(image_name, tag)
        case _:
            print(f'Warning: Registry: {registry} is not currently supported. Skipping tag update check for image: {image_name}')
    
    return updated_tags
    
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

        updated_tags = build_updated_tags_lists(registry, image_name, tag)

        image_dict = {
            "registry": registry,
            "image_name": image_name,
            "tag": tag,
            "updated_tags": updated_tags
        }

        image_dicts.append(image_dict)

    return image_dicts


def get_current_context():
    if cmd :=subprocess.run(["kubectl", "config", "current-context"], capture_output=True, text=True, check=True):
        return cmd.stdout.strip()


if __name__ == "__main__":
    p = argparse.ArgumentParser()

    p.add_argument('-k', '--kube-context',
                   help='Context for kubectl. Default: current-context')
    p.add_argument('-o', '--output-file',
                   help='Output filename. Default: "image_upgrades.json"')

    args = p.parse_args()

    kube_context = args.kube_context or get_current_context()
    
    images = get_all_images(kube_context)

    image_dicts = build_image_dicts(images)
    
    filename = args.output_file or 'image_upgrades.json'
    with open(filename, "w") as out_file:
        json.dump(image_dicts, out_file, indent = 2)
