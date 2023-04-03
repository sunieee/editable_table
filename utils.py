import subprocess
import os

def check_output(command):
    # Run the command with shell=True
    print('[running command:]', command)
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)

    # Read and print the output line by line
    output = ''
    for line in process.stdout:
        print(line.strip())
        output += line

    # Wait for the command to finish and get the return code
    returncode = process.wait()

    # Check the return code (0 means success)
    if returncode == 0:
        return output.strip()
    else:
        return ''
    

def get_local_image_id(image_name):
    try:
        return check_output("docker image inspect --format '{{.Id}}' " + image_name)
    except:
        return ''

def get_docker_image_id(image):
    image_name, tag = image.split(':')
    TOKEN = check_output(f'''curl -s "https://auth.docker.io/token?service=registry.docker.io&scope=repository:{image_name}:pull" | jq -r .token''')
    return check_output(f'''url -s -H "Authorization: Bearer ${TOKEN}" -H 'Accept: application/vnd.docker.distribution.manifest.v2+json' "https://registry-1.docker.io/v2/{image_name}/manifests/{tag}" | jq -r '.config.digest''')


def get_sensetime_image_id(image):
    image_name, tag = image.split(':')
    TOKEN = check_output('''jq -r '.auths["registry.sensetime.com"].auth' ~/.docker/config.json''')
    return check_output(f'''curl -s -H "Authorization: Basic {TOKEN}" -H 'Accept: application/vnd.docker.distribution.manifest.v2+json' "https://registry.sensetime.com/v2/{image_name}/manifests/{tag}" | jq -r '.config.digest''')


def check_identical(image):
    if image.count(':') == 0:
        image += ':latest'
    sensetime_image = "xlab/" + image.split('/')[-1]
    print('sensetime image', sensetime_image)

    if get_docker_image_id(image) == get_sensetime_image_id(sensetime_image):
        return f'registry.sensetime.com/{sensetime_image}'
    return ''


def pull_image(image):
    if image.count(':') == 0:
        image += ':latest'
    print(check_output("docker pull " + image))


def upload_image(image, save=False):
    if image.count(':') == 0:
        image += ':latest'
    sensetime_image = "xlab/" + image.split('/')[-1]
    check_output(f"docker rmi registry.sensetime.com/{sensetime_image} && docker tag {image} registry.sensetime.com/{sensetime_image} && docker push registry.sensetime.com/{sensetime_image}")
    if not save:
        # 删除源镜像，必须要将所有tag都删除，才会把镜像删除！
        check_output(f'docker rmi {image} registry.sensetime.com/{sensetime_image}')
    return f'registry.sensetime.com/{sensetime_image}'


def upload_once(image='hiha3456/swin_ocsr:test'):
    # image = 'pytorch/pytorch:1.9.1-cuda11.1-cudnn8-devel'
    if not check_identical(image):
        pull_image(image)
        upload_image(image, save=False)


def upload_every(image='cyrusmay/openfold:latest'):
    # a threading checking database everyday and add task
    if not check_identical(image):
        pull_image(image)
        upload_image(image, save=True)


if __name__ == '__main__':
    upload_once('codeskyblue/gohttpserver')