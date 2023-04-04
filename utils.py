import subprocess
import os

def check_output(command, verbose=True):
    # Run the command with shell=True
    if verbose:
        print('[running command:]', command)
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)

    # Read and print the output line by line
    output = ''
    for line in process.stdout:
        if verbose:
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
    MANIFEST = check_output(f'''curl -s -H "Authorization: Bearer {TOKEN}" -H 'Accept: application/vnd.docker.distribution.manifest.v2+json' "https://registry-1.docker.io/v2/{image_name}/manifests/{tag}" ''', verbose=False)
    try:
        size = sum([int(x) for x in check_output(f"echo '{MANIFEST}' | jq '.layers[].size' ", verbose=False).split('\n')])
        size = round(size  / 1024 / 1024, 4)
    except:
        size = -1
    return check_output(f"echo '{MANIFEST}' | jq -r '.config.digest' ", verbose=False), size


def get_sensetime_image_id(image):
    image_name, tag = image.split(':')
    TOKEN = check_output('''jq -r '.auths["registry.sensetime.com"].auth' ~/.docker/config.json''')
    return check_output(f'''curl -s -H "Authorization: Basic {TOKEN}" -H 'Accept: application/vnd.docker.distribution.manifest.v2+json' "https://registry.sensetime.com/v2/{image_name}/manifests/{tag}" | jq -r '.config.digest' ''')


def check_identical(image, sensetime_image):
    a, size = get_docker_image_id(image)
    b = get_sensetime_image_id(sensetime_image)
    if not a or a == 'null':
        return 'NotFound', size
    if a == b:
        return 'Identical', size
    return 'NotIdentical', size


def pull_image(image):
    check_output("docker pull " + image)

def upload_image(image, sensetime_image, save=False):
    check_output(f"docker rmi registry.sensetime.com/{sensetime_image}")
    check_output(f"docker tag {image} registry.sensetime.com/{sensetime_image}")
    check_output(f"docker push registry.sensetime.com/{sensetime_image}")
    if not save:
        # 删除源镜像，必须要将所有tag都删除，才会把镜像删除！
        check_output(f'docker rmi registry.sensetime.com/{sensetime_image}')
        check_output(f'docker rmi {image}')

def upload_once(image='hiha3456/swin_ocsr:test'):
    # image = 'pytorch/pytorch:1.9.1-cuda11.1-cudnn8-devel'
    if image.count(':') == 0:
        image += ':latest'
    sensetime_image = "xlab/" + image.split('/')[-1]
    print('sensetime image', sensetime_image)

    ret, size = check_identical(image, sensetime_image)
    print('total size', size)
    if ret == 'NotFound':
        print('source image not found')
        return ''
    if ret == 'NotIdentical':
        pull_image(image)
        upload_image(image, sensetime_image, save=False)

    return f'registry.sensetime.com/{sensetime_image}'


if __name__ == '__main__':
    # upload_once('codeskyblue/gohttpserver')
    upload_once('pytorch/pytorch:1.9.1-cuda11.1-cudnn8-devel')