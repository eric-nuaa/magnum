#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

"""Magnum Kubernetes RPC handler."""

from magnum.conductor.handlers.common import kube_utils
from magnum.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class Handler(object):
    """These are the backend operations.  They are executed by the backend
         service.  API calls via AMQP (within the ReST API) trigger the
         handlers to be called.

         This handler acts as an interface to executes kubectl command line
         services.
    """

    def __init__(self):
        super(Handler, self).__init__()
        self.kube_cli = kube_utils.KubeClient()

    def service_create(self, ctxt, service):
        LOG.debug("service_create")
        # trigger a kubectl command
        status = self.kube_cli.service_create(service)
        if not status:
            return None
        # call the service object to persist in db
        service.create(ctxt)
        return service

    def service_update(self, ctxt, service):
        LOG.debug("service_update")
        # trigger a kubectl command
        status = self.kube_cli.service_update(service)
        if not status:
            return None
        # call the service object to persist in db
        service.refresh(ctxt)
        return service

    def service_list(self, ctxt):
        LOG.debug("service_list")
        return self.kube_cli.service_list()

    def service_delete(self, ctxt, service):
        LOG.debug("service_delete")
        # trigger a kubectl command
        status = self.kube_cli.service_delete(service.uuid)
        if not status:
            return None
        # call the service object to persist in db
        service.destroy(ctxt)

    def service_get(self, ctxt, uuid):
        LOG.debug("service_get")
        return self.kube_cli.service_get(uuid)

    def service_show(self, uuid):
        LOG.debug("service_show")
        return self.kube_cli.service_show(uuid)

    # Pod Operations
    def pod_create(self, ctxt, pod):
        LOG.debug("pod_create")
        # trigger a kubectl command
        status = self.kube_cli.pod_create(pod)
        if not status:
            return None
        # call the pod object to persist in db
        pod.create(ctxt)
        return pod

    def pod_update(self, ctxt, pod):
        LOG.debug("pod_update")
        # trigger a kubectl command
        status = self.kube_cli.pod_update(pod)
        if not status:
            return None
        # call the pod object to persist in db
        pod.refresh(ctxt)
        return pod

    def pod_list(self, ctxt):
        LOG.debug("pod_list")
        return self.kube_cli.pod_list()

    def pod_delete(self, ctxt, pod):
        LOG.debug("pod_delete ")
        # trigger a kubectl command
        status = self.kube_cli.pod_delete(pod.uuid)
        if not status:
            return None
        # call the pod object to persist in db
        pod.destroy(ctxt)

    def pod_get(self, ctxt, uuid):
        LOG.debug("pod_get")
        return self.kube_cli.pod_get(uuid)

    def pod_show(self, ctxt, uuid):
        LOG.debug("pod_show")
        return self.kube_cli.pod_show(uuid)

    # Replication Controller Operations
    def rc_create(self, ctxt, rc):
        LOG.debug("rc_create")
        # trigger a kubectl command
        status = self.kube_cli.rc_create(rc)
        if not status:
            return None
        # call the rc object to persist in db
        rc.create(ctxt)
        return rc

    def rc_update(self, ctxt, rc):
        LOG.debug("rc_update")
        # trigger a kubectl command
        status = self.kube_cli.rc_update(rc)
        if not status:
            return None
        # call the rc object to persist in db
        rc.refresh(ctxt)
        return rc

    def rc_delete(self, ctxt, rc):
        LOG.debug("rc_delete ")
        # trigger a kubectl command
        status = self.kube_cli.pod_delete(rc.uuid)
        if not status:
            return None
        # call the rc object to persist in db
        rc.destroy(ctxt)
