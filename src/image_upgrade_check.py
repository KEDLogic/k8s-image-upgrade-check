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

def get_auth_token(registry_auth_url, image_name):

    r = requests.get('{}{}:pull'.format(registry_auth_url, image_name))

    token = r.json()['token']
    return token

def get_tag_list(registry_index_url, image_name, auth_token):
    h = {'Authorization': "Bearer {}".format(auth_token)}
    r = requests.get('{}{}/tags/list'.format(registry_index_url, image_name),
                    headers={'Authorization': "Bearer {}".format(auth_token)})
    return r.json()

def filter_tag_list(tag_list, tag):
    newer_tags = None
    tags = list(dict.fromkeys(tag_list['tags']))

    try:
        index = int(tags.index(tag))
        newer_tags = tags[index:]
    except ValueError:
        print(f'Warning: {tag_list["name"]} - Cannot filter for newer tags as current tag \"{tag}\" was not found in tag list. All tags will be listed.')
        newer_tags = tags
    
    return newer_tags

def build_updated_tags_lists(registry_auth_url, registry_index_url, image_name, tag):
    auth_token = get_auth_token(registry_auth_url, image_name)
    tag_list = get_tag_list(registry_index_url, image_name, auth_token)
    updated_tags = filter_tag_list(tag_list, tag)

    return updated_tags
    
def build_image_dicts(images, registries):
    image_dicts = []

    for image in images:
        image_name = image.split(':')[0]
        tag = image.split(':')[1]

        if match := re.search("^.*\.[a-z]*$", image_name.split('/')[0]):
            registry = match[0]
            image_name = '/'.join(image_name.split('/')[1:])
        else:
            registry = 'docker.io'

        updated_tags = []
        try:
            if registries[registry]:
                registry_auth_url = registries[registry]['auth_url']
                registry_index_url = registries[registry]['index_url']

                updated_tags = build_updated_tags_lists(registry_auth_url, registry_index_url, image_name, tag)
        except KeyError:
            print(f'Warning: No entry for \"{registry}\" in registries.json. Skipping tag update check for image: {image_name}')
            updated_tags = False

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
                   help='Context for kubectl. Defaults to current-context if not set')

    args = p.parse_args()

    kube_context = args.kube_context or get_current_context()
    
    images = get_all_images(kube_context)

    with open('registries.json') as registries_file:
        registries = json.load(registries_file)

        image_dicts = build_image_dicts(images, registries)

        with open('image_updrades.json', "w") as out_file:
            json.dump(image_dicts, out_file, indent = 2)
