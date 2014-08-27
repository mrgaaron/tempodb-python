import json
from query.selection import AndClause


class TempoIQEncoder(json.JSONEncoder):
    def encode_point(self, point):
        return {
            't': self.encode_datetime(point.timestamp),
            'v': point.value}

    def encode_datetime(self, dt):
        return dt.isoformat()


class WriteEncoder(TempoIQEncoder):
    encoders = {
        'Device': 'encode_device',
        'Sensor': 'encode_sensor',
        'Point': 'encode_point',
        'datetime': 'encode_datetime'
    }

    def default(self, o):
        encoder_name = self.encoders.get(o.__class__.__name__)
        if encoder_name is None:
            super(TempoIQEncoder, self).default(o)
        encoder = getattr(self, encoder_name)
        return encoder(o)

    def encode_device(self, device):
        return device.key

    def encode_sensor(self, sensor):
        return sensor.key


class CreateEncoder(TempoIQEncoder):
    encoders = {
        'Device': 'encode_device',
        'Sensor': 'encode_sensor'
    }

    def default(self, o):
        encoder_name = self.encoders.get(o.__class__.__name__)
        if encoder_name is None:
            super(TempoIQEncoder, self).default(o)
        encoder = getattr(self, encoder_name)
        return encoder(o)

    def encode_device(self, device):
        return {
            'key': device.key,
            'name': device.name,
            'attributes': device.attributes,
            'sensors': map(self.encode_sensor, device.sensors)
        }

    def encode_sensor(self, sensor):
        return {
            'key': sensor.key,
            'name': sensor.name,
            'attributes': sensor.attributes
        }


class ReadEncoder(TempoIQEncoder):
    encoders = {
        'Point': 'encode_point',
        'datetime': 'encode_datetime',
        'ScalarSelector': 'encode_scalar_selector',
        'AndClause': 'encode_compound_clause',
        'OrClause': 'encode_compound_clause',
        'QueryBuilder': 'encode_query_builder',
        'Selection': 'encode_selection',
        'Find': 'encode_function',
        'Interpolation': 'encode_function',
        'MultiRollup': 'encode_function',
        'Rollup': 'encode_function',
        'Aggregation': 'encode_function',
        'ConvertTZ': 'encode_function'
    }

    def default(self, o):
        encoder_name = self.encoders.get(o.__class__.__name__)
        if encoder_name is None:
            super(TempoIQEncoder, self).default(o)
        encoder = getattr(self, encoder_name)
        return encoder(o)

    def encode_compound_clause(self, clause):
        name = None
        if isinstance(clause, AndClause):
            name = 'and'
        else:
            name = 'or'

        return {
            name: map(self.encode_scalar_selector, clause.selectors)
        }

    def encode_function(self, function):
        return {
            'name': function.name,
            'args': function.args
        }

    def encode_query_builder(self, builder):
        j = {
            'search': {
                'select': builder.object_type,
                'filters': {
                    'devices': self.encode_selection(
                        builder.selection['devices']),
                    'sensors': self.encode_selection(
                        builder.selection['sensors'])
                }
            },
            builder.operation.name: builder.operation.args
        }
        if len(builder.pipeline) > 0:
            j['fold'] = {
                'functions': map(self.encode_function, builder.pipeline)

            }
        return j

    def encode_scalar_selector(self, selector):
        return {
            selector.key: selector.value
        }

    def encode_selection(self, selection):
        if selection.selection is None:
            return {}
        if len(selection.selection.selectors) == 0:
            return {}
        return self.encode_compound_clause(selection.selection)