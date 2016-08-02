import contextlib
import os
from os import path
import re
import sys
import time

import docker


@contextlib.contextmanager
def Container(service, ports, extras=None, logs=None):
    client = docker.from_env(assert_hostname=False)
    container, port_map = run_container(client, service, ports, extras)

    try:
        yield port_map
    finally:
        client.stop(container, timeout=0)

        if logs is not None:
            container_output = client.logs(
                container, stdout=True, stderr=True, stream=True,
                timestamps=True
            )
            for line in container_output:
                logs.append(line.decode('utf-8'))

        client.remove_container(container)


def run_container(client, service, ports, extras=None):
    if isinstance(ports, str):
        ports = [ports]
    elif isinstance(ports, int):
        ports = ['{}/tcp'.format(ports)]

    image = _locate_image(client, service)
    image_ports = _get_image_ports(client, image)

    missing_ports = [p for p in ports if p not in image_ports]
    if missing_ports:
        raise RuntimeError('Cannot locate service ports in image')

    volumes = dict(
        (path.abspath(volume), mountpoint)
        for (volume, mountpoint) in extras.get('volumes', {}).items()
    )

    container = client.create_container(
        image=image['Id'],
        ports=ports,
        volumes=list(volumes.keys()) if volumes else None,
        environment=extras.get('environment'),
        host_config=client.create_host_config(
            port_bindings=dict((port, None) for port in ports),
            binds=volumes if volumes else None
        )
    )

    # this can fail with HTTP 404
    client.start(container=container)

    port_map = _get_container_port_mappings(client, container, ports)
    if len(port_map) == 1:
        port_map = list(port_map.values())[0]

    return container['Id'], port_map


def stop_container(client, container, timeout=1, remove=True):
    client.stop(container, timeout=timeout)
    if remove:
        client.remove_container(container)


def _locate_image(client, service):
    id_or_tag = os.environ.get('%s_CONTAINER_IMAGE' % service.upper(), service)

    for image in client.images():
        if image['Id'].startswith('sha256:' + id_or_tag):
            return image

        tags = image.get('RepoTags', [])
        if any(tag.startswith(id_or_tag + ':') for tag in tags):
            return image

    raise ValueError('Cannot locate image for service: {}'.format(service))


def _get_image_ports(client, image):
    image_info = client.inspect_image(image=image)
    return image_info.get('Config', {}).get('ExposedPorts', {}).keys()


def _get_container_port_mappings(client, container, ports):
    container_info = client.inspect_container(container=container)

    match = re.match(r'[a-z]+://(.*):[0-9]+', client.base_url)
    host_ip = match.group(1) if match else '127.0.0.1'  # don't know for sure

    def extract_host_port_mappings():
        for port in ports:
            info = container_info['NetworkSettings']['Ports'][port][0]
            yield port, (
                host_ip if info['HostIp'] == '0.0.0.0' else info['HostIp'],
                int(info['HostPort'])
            )

    return dict(extract_host_port_mappings())
