import contextlib
import os
import re

import docker


@contextlib.contextmanager
def Container(service, ports):
    docker_client = docker.from_env(assert_hostname=False)
    container, port_map = run_container(docker_client, service, ports)
    try:
        yield port_map
    finally:
        stop_container(docker_client, container, remove=True)


def run_container(docker_client, service, ports):
    if isinstance(ports, str):
        ports = [ports]
    elif isinstance(ports, int):
        ports = ['{}/tcp'.format(ports)]

    image = _locate_image(docker_client, service)
    image_ports = _get_image_ports(docker_client, image)

    missing_ports = [p for p in ports if p not in image_ports]
    if missing_ports:
        raise RuntimeError('Cannot locate service ports in image')

    container = docker_client.create_container(
        image=image['Id'],
        ports=ports,
        host_config=docker_client.create_host_config(
            port_bindings=dict((port, None) for port in ports)
        )
    )

    # this can fail with HTTP 404
    docker_client.start(container=container)

    port_map = _get_container_port_mappings(docker_client, container, ports)
    if len(port_map) == 1:
        port_map = list(port_map.values())[0]

    return container['Id'], port_map


def stop_container(docker_client, container, timeout=1, remove=True):
    docker_client.stop(container, timeout=timeout)
    if remove:
        docker_client.remove_container(container)


def _locate_image(docker_client, service):
    id_or_tag = os.environ.get('%s_CONTAINER_IMAGE' % service.upper(), service)

    for image in docker_client.images():
        if image['Id'].startswith('sha256:' + id_or_tag):
            return image

        tags = image.get('RepoTags', [])
        if any(tag.startswith(id_or_tag + ':') for tag in tags):
            return image

    raise ValueError('Cannot locate image for service: {}'.format(service))


def _get_image_ports(docker_client, image):
    image_info = docker_client.inspect_image(image=image)
    return image_info.get('Config', {}).get('ExposedPorts', {}).keys()


def _get_container_port_mappings(docker_client, container, ports):
    container_info = docker_client.inspect_container(container=container)

    match = re.match(r'[a-z]+://(.*):[0-9]+', docker_client.base_url)
    host_ip = match.group(1) if match else '127.0.0.1'  # don't know for sure

    def extract_host_port_mappings():
        for port in ports:
            info = container_info['NetworkSettings']['Ports'][port][0]
            yield port, (
                host_ip if info['HostIp'] == '0.0.0.0' else info['HostIp'],
                int(info['HostPort'])
            )

    return dict(extract_host_port_mappings())
