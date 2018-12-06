from flask_potion.contrib.memory import MemoryManager
from flask_potion import fields, Api, Resource, ModelResource
from tests import BaseTestCase


def TestResource(res_name, sort=None):
    class NewResource(ModelResource):
        class Schema:
            name = fields.String()
            secret = fields.String(io="c")
            slug = fields.String(io="cr")
        class Meta:
            name = res_name
            sort_attribute = sort

    return NewResource


class ModelResourceTestCase(BaseTestCase):

    def setUp(self):
        super(ModelResourceTestCase, self).setUp()
        self.api = Api(self.app, default_manager=MemoryManager)

    def test_schema_io(self):
        FooResource = TestResource("foo")
        self.api.add_resource(FooResource)

        response = self.client.post("/foo", data={
            "name": "Foo",
            "secret": "mystery",
            "slug": "foo"
        })

        self.assert200(response)
        self.assertEqual({
            "$uri": "/foo/1", 
            "name": "Foo",
            "slug": "foo"
        }, response.json)

        self.assertEqual({
            "id": 1,
            "name": "Foo",
            "slug": "foo",
            "secret": "mystery"
        }, FooResource.manager.items[1])

        response = self.client.patch("/foo/1", data={
            "name": "Bar",
            "secret": "123456"
        })

        self.assert400(response)

        response = self.client.patch("/foo/1", data={
            "name": "Bar"
        })

        self.assert200(response)

        self.assertEqual({
            "$uri": "/foo/1",
            "name": "Bar",
            "slug": "foo"
        }, response.json)

        self.assertEqual({
            "id": 1,
            "name": "Bar",
            "slug": "foo",
            "secret": "mystery"
        }, FooResource.manager.items[1])

    def test_sort_attribute(self):
        DescResource = TestResource("desc", sort=("name", True))
        AscResource = TestResource("asc", sort="name")
        UnsortedResource = TestResource("unsorted")

        self.api.add_resource(DescResource)
        self.api.add_resource(AscResource)
        self.api.add_resource(UnsortedResource)

        first_data = {
            "name": "Foo",
            "secret": "mystery",
            "slug": "foo"
        }
        second_data = {
            "name": "Bar",
            "secret": "mystery",
            "slug": "bar"
        }

        self.client.post("/asc", data=first_data)
        self.client.post("/asc", data=second_data)
        self.client.post("/desc", data=first_data)
        self.client.post("/desc", data=second_data)
        self.client.post("/unsorted", data=first_data)
        self.client.post("/unsorted", data=second_data)

        response = self.client.get("/desc").json

        self.assertEqual(response[0]['name'], "Foo")
        self.assertEqual(response[1]['name'], "Bar")

        response = self.client.get("/asc").json
        self.assertEqual(response[0]['name'], "Bar")
        self.assertEqual(response[1]['name'], "Foo")

        response = self.client.get("/unsorted").json

        self.assertEqual(response[0]['name'], "Foo")
        self.assertEqual(response[1]['name'], "Bar")

    def test_inline_schema(self):
        class FooResource(ModelResource):
            class Meta:
                name = "foo"


        class BarResource(ModelResource):
            class Meta:
                name = "bar"

        self.api.add_resource(FooResource)
        self.api.add_resource(BarResource)

        foo = fields.Inline(FooResource)
        foo.bind(BarResource)

        self.assertEqual({'$ref': '/foo/schema'}, foo.response)

    def test_schema_io_create_flag(self):

        class FooResource(ModelResource):
            class Schema:
                name = fields.String()
                slug = fields.String(io="cr")

            class Meta:
                name = "foo"

        self.api.add_resource(FooResource)
        data, code, headers = FooResource().described_by()
        [create_link] = [
            link for link in data['links'] if link['rel'] == 'create']
        [update_link] = [
            link for link in data['links'] if link['rel'] == 'update']
        self.assertEqual({'$ref': '#'}, create_link['schema'])
        self.assertEqual({
                             "type": "object",
                             "additionalProperties": False,
                             "properties": {
                                 "name": {
                                     "type": "string"
                                 }
                             }
                         }, update_link["schema"])
        self.assertEqual(
            ["$uri", "name", "slug"],  sorted(data["properties"].keys()))
