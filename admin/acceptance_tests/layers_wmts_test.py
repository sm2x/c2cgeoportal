# pylint: disable=no-self-use

import pytest

from . import check_grid_headers


@pytest.fixture(scope='class')
@pytest.mark.usefixtures('dbsession')
def layer_wmts_test_data(dbsession):
    from c2cgeoportal_commons.models.main import \
        LayerWMTS, RestrictionArea

    dbsession.begin_nested()

    restrictionareas = []
    for i in range(0, 5):
        restrictionarea = RestrictionArea(
            name='restrictionarea_{}'.format(i))
        dbsession.add(restrictionarea)
        restrictionareas.append(restrictionarea)

    layers = []
    for i in range(0, 25):
        name = 'layer_wmts_{}'.format(i)
        layer = LayerWMTS(name=name)
        layer.layer = name
        layer.url = 'https://server{}.net/wmts'.format(i)
        layer.restrictionareas = [restrictionareas[i % 5],
                                  restrictionareas[(i + 2) % 5]]
        dbsession.add(layer)
        layers.append(layer)

    yield {
        'layers': layers
    }

    dbsession.rollback()


@pytest.mark.usefixtures('layer_wmts_test_data', 'transact', 'test_app')
class TestLayerWMTS():

    def test_view_index_rendering_in_app(self, test_app):
        expected = [('_id_', '', 'false'),
                    ('name', 'Name', 'true'),
                    ('metadata_url', 'Metadata URL', 'true'),
                    ('description', 'Description', 'true'),
                    ('public', 'Public', 'true'),
                    ('geo_table', 'Geo table', 'true'),
                    ('exclude_properties', 'Exclude properties', 'true'),
                    ('url', 'GetCapabilities URL', 'true'),
                    ('layer', 'WMTS layer name', 'true'),
                    ('style', 'Style', 'true'),
                    ('matrix_set', 'Matrix set', 'true'),
                    ('image_type', 'Image type', 'true'),
                    ('dimensions', 'Dimensions', 'false'),
                    ('parents_relation', 'Parents', 'false'),
                    ('interfaces', 'Interfaces', 'true'),
                    ('restrictionareas', 'Restriction areas', 'false'),
                    ('metadatas', 'Metadatas', 'false')]
        check_grid_headers(test_app, '/layers_wmts/', expected)

    def test_grid_complex_column_val(self, test_app, layer_wmts_test_data):
        json = test_app.post(
            '/layers_wmts/grid.json',
            params={
                'current': 1,
                'rowCount': 10,
                'sort[name]': 'asc'
            },
            status=200
        ).json
        row = json['rows'][0]

        layer = layer_wmts_test_data['layers'][0]

        assert layer.id == int(row['_id_'])
        assert layer.name == row['name']

    def test_left_menu(self, test_app):
        html = test_app.get('/layers_wmts/', status=200).html
        main_menu = html.select_one('a[href="http://localhost/layers_wmts/"]').getText()
        assert 'WMTS Layers' == main_menu
