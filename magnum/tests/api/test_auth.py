# Copyright 2014
# The Cloudscaling Group, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mock
from oslo.config import fixture

from magnum.api import auth
from magnum.tests import base
from magnum.tests import fakes


@mock.patch('magnum.api.middleware.auth_token.AuthTokenMiddleware',
            new_callable=fakes.FakeAuthProtocol)
class TestAuth(base.BaseTestCase):

    def setUp(self):
        super(TestAuth, self).setUp()
        self.CONF = self.useFixture(fixture.Config())
        self.app = fakes.FakeApp()

    def test_check_auth_option_enabled(self, mock_auth):
        self.CONF.config(enable_authentication=True)
        result = auth.install(self.app, self.CONF.conf, ['/'])
        self.assertIsInstance(result, fakes.FakeAuthProtocol)

    def test_check_auth_option_disabled(self, mock_auth):
        self.CONF.config(enable_authentication=False)
        result = auth.install(self.app, self.CONF.conf, ['/'])
        self.assertIsInstance(result, fakes.FakeApp)
