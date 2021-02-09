from unittest import TestCase, skip
from unittest.mock import Mock, patch, call
from sqlalchemy.orm.exc import NoResultFound
from commandline import commandlinetools
from argparse import Namespace


class TestListNodesAndSensors(TestCase):
    def test_print_existing_things_displays_correct_things(self):
        expected_result = "Existing Sensors\n\n01 05 \n\n"
        returned_result = commandlinetools._layout_existing_things(
            thing_name="sensor", existing_things=[1, 5]
        )
        self.assertEqual(expected_result, returned_result)

    def test_layout_existing_things_handles_empty_lists(self):
        expected_result = "No existing nodes in database"
        returned_result = commandlinetools._layout_existing_things("node", [])
        self.assertEqual(expected_result, returned_result)
        expected_result = "No existing sensors in database"
        returned_result = commandlinetools._layout_existing_things("sensor", [])
        self.assertEqual(expected_result, returned_result)

    def test_convert_integer_to_string(self):
        self.assertEqual("0x02", commandlinetools._convert_integer_to_string(2))
        self.assertEqual("0x03", commandlinetools._convert_integer_to_string(3))
        self.assertEqual(
            "test string", commandlinetools._convert_integer_to_string("test string")
        )

    def test_layout_thing_details(self):
        data = {
            "Sensor_ID": 1,
            "Node_ID": 2,
            "Name": "Sensor name",
            "Quantity": "Temperature",
        }
        expected_result = """Details for sensor ID 1:

Sensor_ID -- 0x01
Node_ID -- 0x02
Name -- Sensor name
Quantity -- Temperature

"""
        returned_result = commandlinetools._layout_thing_details(
            thing_name="sensor", thing_id=1, thing_data=data
        )
        self.assertEqual(expected_result, returned_result)
        data = {
            "Node_ID": 2,
            "Name": "Node name",
            "Location": "A location",
        }
        expected_result = """Details for node ID 2:

Node_ID -- 0x02
Name -- Node name
Location -- A location

"""
        returned_result = commandlinetools._layout_thing_details(
            thing_name="node", thing_id=2, thing_data=data
        )
        self.assertEqual(expected_result, returned_result)


class TestNodeHelperFunctions(TestCase):
    @patch("builtins.print")
    @patch("commandline.commandlinetools._layout_existing_things", autospec=True)
    @patch("database.database.get_all_node_ids", autospec=True)
    def test_list_nodes(
        self, mock_get_all_node_ids, mock_layout_existing_things, mock_print
    ):
        mock_get_all_node_ids.return_value = [1, 2, 3]
        mock_layout_existing_things.return_value = "Hello World"
        commandlinetools.list_nodes("dummy_args")
        mock_get_all_node_ids.assert_called_once()
        mock_layout_existing_things.assert_called_once_with(
            thing_name="node", existing_things=[1, 2, 3]
        )
        mock_print.assert_called_once_with("Hello World")

        mock_get_all_node_ids.reset_mock()
        mock_layout_existing_things.reset_mock()
        mock_print.reset_mock()
        mock_get_all_node_ids.return_value = [4, 5, 6]
        mock_layout_existing_things.return_value = "Hello Mars"
        commandlinetools.list_nodes("dummy_args")
        mock_get_all_node_ids.assert_called_once()
        mock_layout_existing_things.assert_called_once_with(
            thing_name="node", existing_things=[4, 5, 6]
        )
        mock_print.assert_called_once_with("Hello Mars")

    @patch("builtins.print")
    @patch("commandline.commandlinetools._layout_thing_details", autospec=True)
    @patch("database.database.get_node_data", autospec=True)
    def test_show_node_details(
        self, mock_get_node_data, mock_layout_thing_details, mock_print
    ):
        test_args = Namespace(
            func=commandlinetools.show_node_details,
            id=100,
        )
        mock_get_node_data.return_value = {"a": 1}
        mock_layout_thing_details.return_value = "Hello World"
        commandlinetools.show_node_details(test_args)
        mock_get_node_data.assert_called_once_with(100)
        mock_layout_thing_details.assert_called_once_with(
            thing_name="node", thing_id=100, thing_data={"a": 1}
        )
        mock_print.assert_called_once_with("Hello World")

        mock_get_node_data.reset_mock()
        mock_layout_thing_details.reset_mock()
        mock_print.reset_mock()
        mock_get_node_data.return_value = {"b": 2}
        mock_layout_thing_details.return_value = "Hello Mars"
        test_args = Namespace(
            func=commandlinetools.show_node_details,
            id=95,
        )
        commandlinetools.show_node_details(test_args)
        mock_get_node_data.assert_called_once_with(95)
        mock_layout_thing_details.assert_called_once_with(
            thing_name="node", thing_id=95, thing_data={"b": 2}
        )
        mock_print.assert_called_once_with("Hello Mars")

        mock_get_node_data.side_effect = NoResultFound("error message")
        mock_print.reset_mock()
        commandlinetools.show_node_details(test_args)
        mock_print.assert_called_once_with("Error message")

        mock_get_node_data.side_effect = NoResultFound("error message 2")
        mock_print.reset_mock()
        commandlinetools.show_node_details(test_args)
        mock_print.assert_called_once_with("Error message 2")

    @patch("builtins.print")
    @patch("database.database.add_node", autospec=True)
    def test_add_node_to_database(self, mock_add_node_to_database, mock_print):
        test_args = Namespace(
            func=commandlinetools.add_node_to_database,
            id=34,
            location="Test location",
            name="Test name",
        )
        commandlinetools.add_node_to_database(test_args)
        mock_add_node_to_database.assert_called_once_with(
            node_id=34,
            name="Test name",
            location="Test location",
        )
        mock_print.assert_called_once_with("Node ID 0x22 created in database\n")
        test_args = Namespace(
            func=commandlinetools.add_node_to_database,
            id=35,
            location="Test location 2",
            name="Test name 2",
        )
        commandlinetools.add_node_to_database(test_args)
        mock_add_node_to_database.assert_called_with(
            node_id=35,
            name="Test name 2",
            location="Test location 2",
        )
        mock_print.reset_mock()
        mock_add_node_to_database.side_effect = [
            ValueError("error message"),
            TypeError("other error message"),
        ]
        commandlinetools.add_node_to_database(test_args)
        mock_print.assert_called_once_with(
            "Unable to create node ID 0x23 -- error message\n"
        )
        mock_print.reset_mock()
        commandlinetools.add_node_to_database(test_args)
        mock_print.assert_called_once_with(
            "Unable to create node ID 0x23 -- other error message\n"
        )

    @patch("builtins.print")
    @patch("commandline.commandlinetools._layout_thing_details", autospec=True)
    @patch("database.database.get_sensor_data", autospec=True)
    def test_show_sensor_details(
        self, mock_get_sensor_data, mock_layout_thing_details, mock_print
    ):
        test_args = Namespace(
            func=commandlinetools.show_sensor_details,
            id=100,
        )
        mock_get_sensor_data.return_value = {"a": 1}
        mock_layout_thing_details.return_value = "Hello World"
        commandlinetools.show_sensor_details(test_args)
        mock_get_sensor_data.assert_called_once_with(100)
        mock_layout_thing_details.assert_called_once_with(
            thing_name="sensor", thing_id=100, thing_data={"a": 1}
        )
        mock_print.assert_called_once_with("Hello World")

        mock_get_sensor_data.reset_mock()
        mock_layout_thing_details.reset_mock()
        mock_print.reset_mock()
        mock_get_sensor_data.return_value = {"b": 2}
        mock_layout_thing_details.return_value = "Hello Mars"
        test_args = Namespace(
            func=commandlinetools.show_sensor_details,
            id=95,
        )
        commandlinetools.show_sensor_details(test_args)
        mock_get_sensor_data.assert_called_once_with(95)
        mock_layout_thing_details.assert_called_once_with(
            thing_name="sensor", thing_id=95, thing_data={"b": 2}
        )
        mock_print.assert_called_once_with("Hello Mars")

        mock_get_sensor_data.side_effect = NoResultFound("error message")
        mock_print.reset_mock()
        commandlinetools.show_sensor_details(test_args)
        mock_print.assert_called_once_with("Error message")

        mock_get_sensor_data.side_effect = NoResultFound("error message 2")
        mock_print.reset_mock()
        commandlinetools.show_sensor_details(test_args)
        mock_print.assert_called_once_with("Error message 2")

    @patch("builtins.print")
    @patch("database.database.add_sensor", autospec=True)
    def test_add_sensor_to_database(self, mock_add_sensor_to_database, mock_print):
        test_args = Namespace(
            func=commandlinetools.add_sensor_to_database,
            id=34,
            node=23,
            name="Test name",
            quantity="Test Quantity",
        )
        commandlinetools.add_sensor_to_database(test_args)
        mock_add_sensor_to_database.assert_called_once_with(
            sensor_id=34,
            node_id=23,
            name="Test name",
            quantity="Test Quantity",
        )
        mock_print.assert_called_once_with("Sensor ID 0x22 created in database\n")
        test_args = Namespace(
            func=commandlinetools.add_sensor_to_database,
            id=46,
            node=35,
            name="Test name 2",
            quantity="Test Quantity 2",
        )
        commandlinetools.add_sensor_to_database(test_args)
        mock_add_sensor_to_database.assert_called_with(
            sensor_id=46,
            node_id=35,
            name="Test name 2",
            quantity="Test Quantity 2",
        )
        mock_print.reset_mock()
        mock_add_sensor_to_database.side_effect = [
            ValueError("error message"),
            TypeError("other error message"),
        ]
        commandlinetools.add_sensor_to_database(test_args)
        mock_print.assert_called_once_with(
            "Unable to create sensor ID 0x2e -- error message\n"
        )
        mock_print.reset_mock()
        commandlinetools.add_sensor_to_database(test_args)
        mock_print.assert_called_once_with(
            "Unable to create sensor ID 0x2e -- other error message\n"
        )


class TestSensorHelperFunctions(TestCase):
    @patch("builtins.print")
    @patch("commandline.commandlinetools._layout_existing_things", autospec=True)
    @patch("database.database.get_all_sensor_ids", autospec=True)
    def test_list_sensors(
        self, mock_get_all_sensors, mock_layout_existing_things, mock_print
    ):
        mock_get_all_sensors.return_value = [1, 2, 3]
        mock_layout_existing_things.return_value = "Hello World"
        commandlinetools.list_sensors("")
        mock_get_all_sensors.assert_called_once()
        mock_layout_existing_things.assert_called_once_with(
            thing_name="sensor", existing_things=[1, 2, 3]
        )
        mock_print.assert_called_once_with("Hello World")

        mock_get_all_sensors.reset_mock()
        mock_layout_existing_things.reset_mock()
        mock_print.reset_mock()
        mock_get_all_sensors.return_value = [4, 5, 6]
        mock_layout_existing_things.return_value = "Hello Mars"
        commandlinetools.list_sensors("")
        mock_layout_existing_things.assert_called_once_with(
            thing_name="sensor", existing_things=[4, 5, 6]
        )
        mock_print.assert_called_once_with("Hello Mars")


class TestSetupArgparseForNodes(TestCase):
    @patch("argparse.ArgumentParser")
    def test_argparse_setup_for_nodes(self, mock_argparse):
        mock_argparse.return_value = Mock()
        mock_parser = commandlinetools.setup_node_argparse()
        mock_argparse.assert_called_once()
        mock_parser.add_subparsers.assert_called_once_with(
            help="commands to add nodes and display information about nodes"
        )
        calls = [
            call(help="commands to add nodes and display information about nodes"),
            call().add_parser("list", help="list all existing nodes"),
            call().add_parser().set_defaults(func=commandlinetools.list_nodes),
            call().add_parser("show", help="display information for the node"),
            call()
            .add_parser()
            .add_argument(
                "id",
                type=int,
                help="id for the node to display, an integer in range 0-254",
            ),
            call().add_parser().set_defaults(func=commandlinetools.show_node_details),
            call().add_parser("add", help="add a node to the database"),
            call()
            .add_parser()
            .set_defaults(func=commandlinetools.add_node_to_database),
            call()
            .add_parser()
            .add_argument(
                "id", type=int, help="id for the node to add, an integer in range 0-254"
            ),
            call().add_parser().add_argument("name", help="name for the node to add"),
            call()
            .add_parser()
            .add_argument("location", help="location for the node to add"),
        ]
        mock_parser.add_subparsers.assert_has_calls(calls)

    @patch("commandline.commandlinetools.list_nodes", autospec=True)
    def test_parser_calls_list_node_function(self, mock_list_nodes):
        test_parser = commandlinetools.setup_node_argparse()
        args = test_parser.parse_args(["list"])
        args.func(args)
        mock_list_nodes.assert_called_once_with(args)

    @patch("commandline.commandlinetools.show_node_details", autospec=True)
    def test_parser_calls_show_node_details_function(self, mock_show_node_details):
        test_parser = commandlinetools.setup_node_argparse()
        args = test_parser.parse_args(["show", "2"])
        args.func(args)
        mock_show_node_details.assert_called_once_with(args)

    @patch("commandline.commandlinetools.add_node_to_database", autospec=True)
    def test_parser_calls_add_node(self, mock_add_node):
        test_parser = commandlinetools.setup_node_argparse()
        args = test_parser.parse_args(["add", "2", "Node Name", "Node location"])
        args.func(args)
        mock_add_node.assert_called_once_with(args)

    @patch("argparse.ArgumentParser")
    def test_argparse_setup_for_sensors(self, mock_argparse):
        mock_argparse.return_value = Mock()
        mock_parser = commandlinetools.setup_sensor_argparse()
        mock_argparse.assert_called_once()
        mock_parser.add_subparsers.assert_called_once_with(
            help="commands to add sensors and display information about sensors"
        )
        calls = [
            call(help="commands to add sensors and display information about sensors"),
            call().add_parser("list", help="list all existing sensors"),
            call().add_parser().set_defaults(func=commandlinetools.list_sensors),
            call().add_parser("show", help="display information for the sensor"),
            call()
            .add_parser()
            .add_argument(
                "id",
                type=int,
                help="id for the sensor to display, an integer in range 0-254",
            ),
            call().add_parser().set_defaults(func=commandlinetools.show_sensor_details),
            call().add_parser("add", help="add a sensor to the database"),
            call()
            .add_parser()
            .set_defaults(func=commandlinetools.add_sensor_to_database),
            call()
            .add_parser()
            .add_argument(
                "id",
                type=int,
                help="id for the sensor to add, an integer in range 0-254",
            ),
            call()
            .add_parser()
            .add_argument(
                "node",
                type=int,
                help="id for the node of sensor to add, an integer in range 0-254",
            ),
            call().add_parser().add_argument("name", help="name for the sensor to add"),
            call()
            .add_parser()
            .add_argument("quantity", help="quantity for the sensor to add"),
        ]
        mock_parser.add_subparsers.assert_has_calls(calls)
