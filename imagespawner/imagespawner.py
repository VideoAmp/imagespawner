from dockerspawner import DockerSpawner
from kubespawner import KubeSpawner
from re import match
from traitlets import (
    default,
    observe,
    HasTraits,
    List,
    Unicode,
)
from tornado import gen
from tornado.escape import xhtml_escape


class ImageChooserMixin(HasTraits):

    dockerimages = List(
        trait = Unicode(),
        default_value = ['jupyterhub/singleuser'],
        minlen = 1,
        config = True,
        help = "Predefined Docker images."
    )

    form_template = Unicode("""
        <label for="dockerimage">Select a Docker image:</label>
        <select class="form-control" name="dockerimage" required autofocus>
            {option_template}
        </select>
        <label for="dockercustomimage">Alternatively enter an image name:</label>
        <input class="form-control" type="text" name="dockercustomimage" />
        """,
        config = True,
        help = "Form template."
    )

    option_template = Unicode("""
        <option value="{image}">{image}</option>
        """,
        config = True,
        help = "Template for html form options."
    )

    @default('options_form')
    def _options_form(self):
        """Return the form with the drop-down menu."""
        dockerimages = ['videoamp/notebook-{username}'.format(username=self.user.name)] + self.dockerimages
        options = ''.join([
            self.option_template.format(image=di) for di in dockerimages
        ])
        return self.form_template.format(option_template=options)

    def options_from_form(self, formdata):
        """Parse the submitted form data and turn it into the correct
           structures for self.user_options."""

        default = self.dockerimages[0]

        # formdata looks like {'dockerimage': ['jupyterhub/singleuser']}"""
        dockerimage = formdata.get('dockerimage', [default])[0]
        dockercustomimage = formdata.get('dockercustomimage')[0]

        if dockercustomimage:
            dockerimage = dockercustomimage

        options = {
            'container_image': dockerimage,
        }
        return options


class DockerImageChooserSpawner(ImageChooserMixin, DockerSpawner):
    '''Enable the user to select the docker image that gets spawned.

    Define the available docker images in the JupyterHub configuration and pull
    them to the execution nodes:

    c.JupyterHub.spawner_class = DockerImageChooserSpawner
    c.DockerImageChooserSpawner.dockerimages = [
        'jupyterhub/singleuser',
        'jupyter/r-singleuser'
    ]
    '''

    @gen.coroutine
    def start(self, image=None, extra_create_kwargs=None,
            extra_start_kwargs=None, extra_host_config=None):
        # container_prefix is used to construct container_name
        self.container_prefix = '{}-{}'.format(
            super().container_prefix,
            self.user_options['container_image'].replace('/', '-')
        )

        # start the container
        ip, port = yield DockerSpawner.start(
            self, image=self.user_options['container_image'],
            extra_create_kwargs=extra_create_kwargs,
            extra_host_config=extra_host_config)
        return ip, port


class KubeImageChooserSpawner(ImageChooserMixin, KubeSpawner):
    '''Enable the user to select the docker image that gets spawned.

    Define the available docker images in the JupyterHub configuration:

    c.JupyterHub.spawner_class = KubeImageChooserSpawner
    c.KubeImageChooserSpawner.dockerimages = [
        'jupyterhub/singleuser',
        'jupyter/r-singleuser'
    ]
    '''

    @observe('user_options')
    def _update_options(self, change):
        options = change.new
        if 'container_image' in options:
            self.singleuser_image_spec = options['container_image']


# http://jupyter.readthedocs.io/en/latest/development_guide/coding_style.html
# vim: set ai et ts=4 sw=4:
