# Copyright 2014 NEC Corporation.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from magnum.conductor.handlers.common import kube_utils
from magnum import objects
from magnum.tests import base

import mock
from mock import patch


class TestKubeUtils(base.BaseTestCase):
    def setUp(self):
        super(TestKubeUtils, self).setUp()

    def test_extract_resource_type(self):
        expected_resource_type = 'bay'

        bay = objects.Bay({})
        actual_type = kube_utils._extract_resource_type(bay)
        self.assertEqual(expected_resource_type, actual_type)

    @patch('magnum.conductor.handlers.common.kube_utils.'
           '_extract_resource_type')
    def test_extract_resource_data_with_data(self,
                                             mock_extract_resource_type):
        expected_data = 'expected_data'

        mock_extract_resource_type.return_value = 'mock_type'
        mock_resource = mock.MagicMock()
        mock_resource.mock_type_data = expected_data
        actual_data = kube_utils._extract_resource_data(mock_resource)
        self.assertEqual(expected_data, actual_data)

    @patch('magnum.conductor.handlers.common.kube_utils.'
           '_extract_resource_type')
    def test_extract_resource_definition_url(self,
                                             mock_extract_resource_type):
        expected_data = 'expected_url'

        mock_extract_resource_type.return_value = 'mock_type'
        mock_resource = mock.MagicMock()
        mock_resource.mock_type_definition_url = expected_data
        actual_data = kube_utils._extract_resource_definition_url(
            mock_resource)
        self.assertEqual(expected_data, actual_data)

    @patch('magnum.conductor.handlers.common.kube_utils._k8s_create_with_data')
    @patch('magnum.conductor.handlers.common.kube_utils.'
           '_extract_resource_data')
    @patch('magnum.conductor.handlers.common.kube_utils.'
            '_extract_resource_definition_url')
    def test_k8s_create_data(self,
                             mock_definition_url,
                             mock_data,
                             mock_create_with_data):
        expected_data = 'data'
        master_address = 'master_address'
        mock_data.return_value = expected_data
        mock_definition_url.return_value = None
        mock_resource = mock.MagicMock()

        kube_utils._k8s_create(master_address, mock_resource)
        mock_create_with_data.assert_called_once_with(master_address,
                                                      expected_data)

    @patch('magnum.conductor.handlers.common.kube_utils._k8s_create_with_path')
    @patch('magnum.conductor.handlers.common.kube_utils.'
           '_extract_resource_data')
    @patch('magnum.conductor.handlers.common.kube_utils.'
            '_extract_resource_definition_url')
    def test_k8s_create_url(self,
                             mock_definition_url,
                             mock_data,
                             mock_create_with_path):
        expected_url = 'url'
        master_address = 'master_address'
        mock_data.return_value = None
        mock_definition_url.return_value = expected_url
        mock_resource = mock.MagicMock()

        kube_utils._k8s_create(master_address, mock_resource)
        mock_create_with_path.assert_called_once_with(master_address,
                                                      expected_url)

    @patch('magnum.openstack.common.utils.trycmd')
    def test_k8s_create_with_path(self, mock_trycmd):
        expected_master_address = 'master_address'
        expected_pod_file = 'pod_file'
        expected_command = [
            'kubectl', 'create',
            '-s', expected_master_address,
            '-f', expected_pod_file
        ]

        kube_utils._k8s_create_with_path(expected_master_address,
                                         expected_pod_file)
        mock_trycmd.assert_called_once_with(*expected_command)

    @patch('magnum.conductor.handlers.common.kube_utils._k8s_create_with_path')
    @patch('tempfile.NamedTemporaryFile')
    def test_k8s_create_with_data(self,
                                  mock_named_tempfile,
                                  mock_k8s_create):
        expected_master_address = 'master_address'
        expected_data = 'resource_data'
        expected_filename = 'resource_file'

        mock_file = mock.MagicMock()
        mock_file.name = expected_filename
        mock_named_tempfile.return_value.__enter__.return_value = mock_file

        kube_utils._k8s_create_with_data(expected_master_address,
            expected_data)

        mock_file.write.assert_called_once_with(expected_data)
        mock_k8s_create.assert_called_once_with(expected_master_address,
                                                expected_filename)

    @patch('magnum.conductor.handlers.common.kube_utils._k8s_update_with_data')
    @patch('magnum.conductor.handlers.common.kube_utils.'
            '_extract_resource_data')
    @patch('magnum.conductor.handlers.common.kube_utils.'
            '_extract_resource_definition_url')
    def test_k8s_update_data(self,
                             mock_definition_url,
                             mock_data,
                             mock_update_with_data):
        expected_data = 'data'
        master_address = 'master_address'
        mock_data.return_value = expected_data
        mock_definition_url.return_value = None
        mock_resource = mock.MagicMock()

        kube_utils._k8s_update(master_address, mock_resource)
        mock_update_with_data.assert_called_once_with(master_address,
                                                      expected_data)

    @patch('magnum.conductor.handlers.common.kube_utils._k8s_update_with_path')
    @patch('magnum.conductor.handlers.common.kube_utils.'
           '_extract_resource_data')
    @patch('magnum.conductor.handlers.common.kube_utils.'
            '_extract_resource_definition_url')
    def test_k8s_update_url(self,
                             mock_definition_url,
                             mock_data,
                             mock_update_with_path):
        expected_url = 'url'
        master_address = 'master_address'
        mock_data.return_value = None
        mock_definition_url.return_value = expected_url
        mock_resource = mock.MagicMock()

        kube_utils._k8s_update(master_address, mock_resource)
        mock_update_with_path.assert_called_once_with(master_address,
                                                      expected_url)

    @patch('magnum.openstack.common.utils.trycmd')
    def test_k8s_update_with_path(self, mock_trycmd):
        expected_master_address = 'master_address'
        expected_pod_file = 'pod_file'
        expected_command = [
            'kubectl', 'update',
            '-s', expected_master_address,
            '-f', expected_pod_file
        ]

        kube_utils._k8s_update_with_path(expected_master_address,
                                         expected_pod_file)
        mock_trycmd.assert_called_once_with(*expected_command)

    @patch('magnum.conductor.handlers.common.kube_utils._k8s_update_with_path')
    @patch('tempfile.NamedTemporaryFile')
    def test_k8s_update_with_data(self,
                                  mock_named_tempfile,
                                  mock_k8s_update):
        expected_master_address = 'master_address'
        expected_data = 'resource_data'
        expected_filename = 'resource_file'

        mock_file = mock.MagicMock()
        mock_file.name = expected_filename
        mock_named_tempfile.return_value.__enter__.return_value = mock_file

        kube_utils._k8s_update_with_data(expected_master_address,
            expected_data)

        mock_file.write.assert_called_once_with(expected_data)
        mock_k8s_update.assert_called_once_with(expected_master_address,
                                                expected_filename)