#!/usr/bin/env python

import contextmanager
import os
import random
import unittest

import docker


class DockerTest(unittest.TestCase):
    """Abstract class to instatiate docker containers as test fixtures."""

    @classmethod
    def setUpClass(cls):
        """Class fixture to ensure test fixtures are called."""
        cls._docker = cls._get_docker_client()
        cls._add_test_fixtures('setUp')
        cls._add_test_fixtures('tearDown')

    @staticmethod
    def _get_docker_client():
        # This could be more elaborate - e.g., connect to a remote docker
        return docker.from_env(assert_hostname=False)

    @classmethod
    def _add_test_fixtures(cls, fixture_name):
        original_fixture = getattr(DockerTest, fixture_name)
        current_fixture = getattr(cls, fixture_name)

        # if class was inherited and fixture was changed
        if cls is not DockerTest and current_fixture is not original_fixture:
            if fixture_name == 'setUp':
                def combined_fixture(self, *args, **kwargs):
                    original_fixture(self)
                    return current_fixture(self, *args, **kwargs)
            elif fixture_name == 'tearDown':
                def combined_fixture(self, *args, **kwargs):
                    result = current_fixture(self, *args, **kwargs)
                    original_fixture(self)
                    return result

            setattr(cls, fixture_name, combined_fixture)

    def setUp(self):
        # GIVEN : service image name and port mappings
        # locate service image
        # create container for service - request port mappings
        # start container
        # identify port mappings
        # build host_port list
        pass

    def tearDown(self):
        # stop container
        # remove container
        pass


@contextmanager
def service(service, ports):
    # setUp
    yield None  # hostports
    # tearDown


# def _get_service_base_url(service):
#     environment_setting = os.environ.get('{}_BASE_URL'.format(service.upper()))
#     if environment_setting is None:
#         container, hostports = _run_container(service, ports=[12345])
#         service_base_urls = [
#             '{scheme}://{hostport}'.format(scheme='http', hostport=hostport)
#             for hostport in hostports
#         ]

#     return service_base_urls


# def _run_container(image, ports=[]):
#     """Creates a docker container for service and ports.

#     Args:
#         image (dict|str): Reference to docker image
#         ports (list[int|str]): List of container ports to map to host.
#             Integers are assumed to be TCP ports. Strings should be
#             formatted as <number>/<proto>, e.g., 1234/udp or 4321/tcp.

#     Returns:
#         container, hostports: Container information and mapped host:port's
#     """

#     image_ports = _get_image_ports(image)
#     service_ports = [port for port in image_ports if port in ports]
#     if not service_ports:
#         raise RuntimeError('Cannot locate service ports in image')

#     container = docker_client.create_container(
#         image=image,
#         ports=service_ports,
#         host_config=docker_client.create_host_config(
#             port_bindings=dict((port, None) for port in service_ports)
#         )
#     )

#     # this can fail with HTTP 404
#     docker_client.start(container=container)
#     return container


# def _stop_container(container, remove=True):
#     docker_client.stop(container)
#     docker_client.remove_container(container)


# def _locate_image(service):
#     id_or_tag = os.environ.get('%s_CONTAINER_IMAGE' % service.upper(), service)

#     for image in docker_client.images():
#         if image['Id'].startswith('sha256:' + id_or_tag):
#             return image

#         tags = image.get('RepoTags', [])
#         if any(tag.startswith(id_or_tag + ':') for tag in tags):
#             return image

#     raise ValueError('Cannot locate image for service: {}'.format(service))


# def _get_image_ports(image):
#     image_info = docker_client.inspect_image(image=image)
#     return image_info.get('Config', {}).get('ExposedPorts', {}).keys()
