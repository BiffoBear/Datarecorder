from unittest import TestCase, skip
from unittest.mock import Mock, patch, call
from sqlalchemy.orm.exc import NoResultFound
from commandline import addnode


class TestListNodesAndSensors(TestCase):

    def test_high_lite_existing_things(self):
        returned_result = addnode._high_lite_existing_things(thing=5, existing_things=[5])
        self.assertEqual(f'\x1b[1m05 \x1b[0m', returned_result)
        returned_result = addnode._high_lite_existing_things(thing=5, existing_things=[4])
        self.assertEqual(f'\x1b[90m05 \x1b[0m', returned_result)

    def test_print_existing_things_displays_correct_things(self):
        expected_result = '''[1mExisting Sensors[0m

[90m00 [0m[1m01 [0m[90m02 [0m[90m03 [0m[90m04 [0m[1m05 [0m[90m06 [0m[90m07 [0m[90m08 [0m[90m09 [0m\
[90m0a [0m[90m0b [0m[90m0c [0m[90m0d [0m[90m0e [0m[90m0f [0m
[90m10 [0m[90m11 [0m[90m12 [0m[90m13 [0m[90m14 [0m[90m15 [0m[90m16 [0m[90m17 [0m[90m18 [0m[90m19 \
[0m[90m1a [0m[90m1b [0m[90m1c [0m[90m1d [0m[90m1e [0m[90m1f [0m
[90m20 [0m[90m21 [0m[90m22 [0m[90m23 [0m[90m24 [0m[90m25 [0m[90m26 [0m[90m27 [0m[90m28 [0m[90m29 \
[0m[90m2a [0m[90m2b [0m[90m2c [0m[90m2d [0m[90m2e [0m[90m2f [0m
[90m30 [0m[90m31 [0m[90m32 [0m[90m33 [0m[90m34 [0m[90m35 [0m[90m36 [0m[90m37 [0m[90m38 [0m[90m39 \
[0m[90m3a [0m[90m3b [0m[90m3c [0m[90m3d [0m[90m3e [0m[90m3f [0m
[90m40 [0m[90m41 [0m[90m42 [0m[90m43 [0m[90m44 [0m[90m45 [0m[90m46 [0m[90m47 [0m[90m48 [0m[90m49 \
[0m[90m4a [0m[90m4b [0m[90m4c [0m[90m4d [0m[90m4e [0m[90m4f [0m
[90m50 [0m[90m51 [0m[90m52 [0m[90m53 [0m[90m54 [0m[90m55 [0m[90m56 [0m[90m57 [0m[90m58 [0m[90m59 \
[0m[90m5a [0m[90m5b [0m[90m5c [0m[90m5d [0m[90m5e [0m[90m5f [0m
[90m60 [0m[90m61 [0m[90m62 [0m[90m63 [0m[90m64 [0m[90m65 [0m[90m66 [0m[90m67 [0m[90m68 [0m[90m69 \
[0m[90m6a [0m[90m6b [0m[90m6c [0m[90m6d [0m[90m6e [0m[90m6f [0m
[90m70 [0m[90m71 [0m[90m72 [0m[90m73 [0m[90m74 [0m[90m75 [0m[90m76 [0m[90m77 [0m[90m78 [0m[90m79 \
[0m[90m7a [0m[90m7b [0m[90m7c [0m[90m7d [0m[90m7e [0m[90m7f [0m
[90m80 [0m[90m81 [0m[90m82 [0m[90m83 [0m[90m84 [0m[90m85 [0m[90m86 [0m[90m87 [0m[90m88 [0m[90m89 \
[0m[90m8a [0m[90m8b [0m[90m8c [0m[90m8d [0m[90m8e [0m[90m8f [0m
[90m90 [0m[90m91 [0m[90m92 [0m[90m93 [0m[90m94 [0m[90m95 [0m[90m96 [0m[90m97 [0m[90m98 [0m[90m99 \
[0m[90m9a [0m[90m9b [0m[90m9c [0m[90m9d [0m[90m9e [0m[90m9f [0m
[90ma0 [0m[90ma1 [0m[90ma2 [0m[90ma3 [0m[90ma4 [0m[90ma5 [0m[90ma6 [0m[90ma7 [0m[90ma8 [0m[90ma9 \
[0m[90maa [0m[90mab [0m[90mac [0m[90mad [0m[90mae [0m[90maf [0m
[90mb0 [0m[90mb1 [0m[90mb2 [0m[90mb3 [0m[90mb4 [0m[90mb5 [0m[90mb6 [0m[90mb7 [0m[90mb8 [0m[90mb9 \
[0m[90mba [0m[90mbb [0m[90mbc [0m[90mbd [0m[90mbe [0m[90mbf [0m
[90mc0 [0m[90mc1 [0m[90mc2 [0m[90mc3 [0m[90mc4 [0m[90mc5 [0m[90mc6 [0m[90mc7 [0m[90mc8 [0m[90mc9 \
[0m[90mca [0m[90mcb [0m[90mcc [0m[90mcd [0m[90mce [0m[90mcf [0m
[90md0 [0m[90md1 [0m[90md2 [0m[90md3 [0m[90md4 [0m[90md5 [0m[90md6 [0m[90md7 [0m[90md8 [0m[90md9 \
[0m[90mda [0m[90mdb [0m[90mdc [0m[90mdd [0m[90mde [0m[90mdf [0m
[90me0 [0m[90me1 [0m[90me2 [0m[90me3 [0m[90me4 [0m[90me5 [0m[90me6 [0m[90me7 [0m[90me8 [0m[90me9 \
[0m[90mea [0m[90meb [0m[90mec [0m[90med [0m[90mee [0m[90mef [0m
[90mf0 [0m[90mf1 [0m[90mf2 [0m[90mf3 [0m[90mf4 [0m[90mf5 [0m[90mf6 [0m[90mf7 [0m[90mf8 [0m[90mf9 \
[0m[90mfa [0m[90mfb [0m[90mfc [0m[90mfd [0m[90mfe [0m

'''
        returned_result = addnode._layout_existing_things(thing_name='sensor', existing_things=[1, 5])
        self.assertEqual(expected_result, returned_result)

    def test_layout_existing_things_handles_empty_lists(self):
        expected_result = 'No existing nodes in database'
        returned_result = addnode._layout_existing_things('node', [])
        self.assertEqual(expected_result, returned_result)
        expected_result = 'No existing sensors in database'
        returned_result = addnode._layout_existing_things('sensor', [])
        self.assertEqual(expected_result, returned_result)

    def test_convert_value_to_string(self):
        self.assertEqual('0x02', addnode._convert_value_to_string(2))
        self.assertEqual('0x03', addnode._convert_value_to_string(3))
        self.assertEqual('test string', addnode._convert_value_to_string('test string'))

    def test_layout_thing_details(self):
        data = {'Sensor_ID': 1,
                'Node_ID': 2,
                'Name': 'Sensor name',
                'Quantity': 'Temperature',
                }
        expected_result = '''Details for sensor ID 1:

Sensor_ID -- 0x01
Node_ID -- 0x02
Name -- Sensor name
Quantity -- Temperature

'''
        returned_result = addnode._layout_thing_details(thing_name='sensor', thing_id=1, thing_data=data)
        self.assertEqual(expected_result, returned_result)
        data = {'Node_ID': 2,
                'Name': 'Node name',
                'Location': 'A location',
                }
        expected_result = '''Details for node ID 2:

Node_ID -- 0x02
Name -- Node name
Location -- A location

'''
        returned_result = addnode._layout_thing_details(thing_name='node', thing_id=2, thing_data=data)
        self.assertEqual(expected_result, returned_result)


class TestHelperFunctions(TestCase):

    @patch('builtins.print')
    @patch('commandline.addnode._layout_existing_things', autospec=True)
    @patch('database.database.get_all_node_ids', autospec=True)
    def test_list_nodes(self, mock_get_all_nodes, mock_layout_existing_things, mock_print):
        mock_get_all_nodes.return_value = [1, 2, 3]
        mock_layout_existing_things.return_value = 'Hello World'
        addnode.list_nodes()
        mock_get_all_nodes.assert_called_once()
        mock_layout_existing_things.assert_called_once_with(thing_name='node',
                                                            existing_things=[1, 2, 3]
                                                            )
        mock_print.assert_called_once_with('Hello World')

        mock_get_all_nodes.reset_mock()
        mock_layout_existing_things.reset_mock()
        mock_print.reset_mock()
        mock_get_all_nodes.return_value = [4, 5, 6]
        mock_layout_existing_things.return_value = 'Hello Mars'
        addnode.list_nodes()
        mock_get_all_nodes.assert_called_once()
        mock_layout_existing_things.assert_called_once_with(thing_name='node',
                                                            existing_things=[4, 5, 6]
                                                            )
        mock_print.assert_called_once_with('Hello Mars')

    @patch('builtins.print')
    @patch('commandline.addnode._layout_thing_details', autospec=True)
    @patch('database.database.get_node_data', autospec=True)
    def test_show_node_details(self, mock_get_node_data, mock_layout_thing_details, mock_print):
        mock_get_node_data.return_value = {'a': 1}
        mock_layout_thing_details.return_value = 'Hello World'
        addnode.show_node_details(node_id=100)
        mock_get_node_data.assert_called_once_with(100)
        mock_layout_thing_details.assert_called_once_with(thing_name='node', thing_id=100, thing_data={'a': 1})
        mock_print.assert_called_once_with('Hello World')

        mock_get_node_data.reset_mock()
        mock_layout_thing_details.reset_mock()
        mock_print.reset_mock()
        mock_get_node_data.return_value = {'b': 2}
        mock_layout_thing_details.return_value = 'Hello Mars'
        addnode.show_node_details(node_id=95)
        mock_get_node_data.assert_called_once_with(95)
        mock_layout_thing_details.assert_called_once_with(thing_name='node', thing_id=95, thing_data={'b': 2})
        mock_print.assert_called_once_with('Hello Mars')

        mock_get_node_data.side_effect = NoResultFound('error message')
        mock_print.reset_mock()
        addnode.show_node_details(node_id=95)
        mock_print.assert_called_once_with('Error message')

        mock_get_node_data.side_effect = NoResultFound('error message 2')
        mock_print.reset_mock()
        addnode.show_node_details(node_id=95)
        mock_print.assert_called_once_with('Error message 2')




class TestSetupArgparseForNodes(TestCase):

    @patch('argparse.ArgumentParser')
    def test_argparse_setup_for_nodes(self, mock_argparse):
        mock_argparse.return_value = Mock()
        mock_parser = addnode.setup_node_argparse()
        mock_argparse.assert_called_once()
        mock_parser.add_subparsers.assert_called_once_with(
            help='commands to add nodes and display information about nodes')
        calls = [call(help='commands to add nodes and display information about nodes'),
                 call().add_parser('list', help='list all existing nodes'),
                 call().add_parser().set_defaults(func=addnode.list_nodes),
                 call().add_parser('show', help='display information for the node'),
                 call().add_parser().add_argument('id', type=int,
                                                  help='id for the node to display, an integer in range 0-254'),
                 call().add_parser().set_defaults(func=addnode.show_node_details),
                 call().add_parser('add', help='display information for the node'),
                 call().add_parser().set_defaults(func=addnode.add_node),
                 call().add_parser().add_argument('id', type=int,
                                                  help='id for the node to add, an integer in range 0-254'),
                 call().add_parser().add_argument('name', help='name for the node to add'),
                 call().add_parser().add_argument('location', help='location for the node to add'),
                 ]
        mock_parser.add_subparsers.assert_has_calls(calls)

    @patch('commandline.addnode.list_nodes', autospec=True)
    def test_parser_calls_list_node_function(self, mock_list_nodes):
        test_parser = addnode.setup_node_argparse()
        args = test_parser.parse_args(['list'])
        args.func()
        mock_list_nodes.assert_called_once()

    @patch('commandline.addnode.show_node_details', autospec=True)
    def test_parser_calls_show_node_details_function(self, mock_show_node_details):
        test_parser = addnode.setup_node_argparse()
        args = test_parser.parse_args(['show', '2'])
        args.func(node_id=args.id)
        mock_show_node_details.assert_called_once_with(node_id=2)

    @patch('commandline.addnode.add_node', autospec=True)
    def test_parser_calls_add_node(self, mock_add_node):
        test_parser = addnode.setup_node_argparse()
        args = test_parser.parse_args(['add', '2', 'Node Name', 'Node location'])
        args.func(node_id=args.id, name=args.name, location=args.location)
        mock_add_node.assert_called_once_with(node_id=2, name='Node Name', location='Node location')
