# Licensed under the Apache License, Version 2.0 (the "License");
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
from magnum.conductor import api
from magnum.tests.db import base as db_base

from mock import patch


class TestBayController(db_base.DbTestCase):
    def simulate_rpc_bay_create(self, bay):
        bay.create()
        return bay

    def test_bay_api(self):
        with patch.object(api.API, 'bay_create') as mock_method:
            # Create a bay
            mock_method.side_effect = self.simulate_rpc_bay_create
            params = '{"name": "bay_example_A", "baymodel_id": "12345", \
                "node_count": "3"}'
            response = self.app.post('/v1/bays',
                                     params=params,
                                     content_type='application/json')
            self.assertEqual(response.status_int, 201)

            # Get all bays
            response = self.app.get('/v1/bays')
            self.assertEqual(response.status_int, 200)
            self.assertEqual(1, len(response.json))
            c = response.json['bays'][0]
            self.assertIsNotNone(c.get('uuid'))
            self.assertEqual('bay_example_A', c.get('name'))
            self.assertEqual(3, c.get('node_count'))

            # Get just the one we created
            response = self.app.get('/v1/bays/%s' % c.get('uuid'))
            self.assertEqual(response.status_int, 200)

            # Update the description
            params = [{'path': '/name',
                       'value': 'bay_example_B',
                       'op': 'replace'}]
            response = self.app.patch_json('/v1/bays/%s' % c.get('uuid'),
                                   params=params)
            self.assertEqual(response.status_int, 200)

            # Delete the bay we created
            response = self.app.delete('/v1/bays/%s' % c.get('uuid'))
            self.assertEqual(response.status_int, 204)

            response = self.app.get('/v1/bays')
            self.assertEqual(response.status_int, 200)
            c = response.json['bays']
            self.assertEqual(0, len(c))
