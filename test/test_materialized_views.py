import unittest
import os.path
import requests_mock
import tableauserverclient as TSC
import samples.materialize_workbooks as mv
from mock import Mock, PropertyMock


TEST_ASSET_DIR = os.path.join(os.path.dirname(__file__), 'assets')

INVALID_DIR = 'INVALID_PATH'
WORKBOOK_NAME_LIST = os.path.join(TEST_ASSET_DIR, 'sample_workbook_name_list.txt')
WORKBOOK_PATH_LIST = os.path.join(TEST_ASSET_DIR, 'sample_workbook_path_list.txt')
WORKBOOK_PATH_LIST_COMMA_SEPARATED = os.path.join(TEST_ASSET_DIR, 'sample_workbook_path_list_comma_separated.txt')


class MaterializedViewsTests(unittest.TestCase):
    def setUp(self):
        self.server = TSC.Server('http://test')

        # Fake signin
        self.server._auth_token = 'j80k54ll2lfMZ0tv97mlPvvSCRyD0DOM'
        self.server._site_id = '0626857c-1def-4503-a7d8-7907c3ff9d9f'
        self.baseurl = self.server.sites.baseurl
        self.all_projects = create_test_projects()

    def test_find_project_path(self):
        project_path = mv.find_project_path(self.all_projects['0'], self.all_projects, "")
        self.assertEqual("project0", project_path)

        project_path = mv.find_project_path(self.all_projects['4'], self.all_projects, "")
        self.assertEqual("project0/project2/project4", project_path)

    def test_find_projects_to_update(self):
        all_projects = [project for project in self.all_projects.values()]
        projects_to_update = []
        mv.find_projects_to_update(self.all_projects['0'], all_projects, projects_to_update)
        self.assertEqual(5, len(projects_to_update))

        projects_to_update = []
        mv.find_projects_to_update(self.all_projects['1'], all_projects, projects_to_update)
        self.assertEqual(2, len(projects_to_update))

    def test_parse_workbook_path_file_not_exists(self):
        workbook_path_mapping = mv.parse_workbook_path(INVALID_DIR)
        self.assertEqual(0, len(workbook_path_mapping))

    def test_parse_workbook_path(self):
        workbook_path_mapping = mv.parse_workbook_path(WORKBOOK_PATH_LIST)
        self.assertEqual(2, len(workbook_path_mapping))
        self.assertEqual('Default', workbook_path_mapping['Book1'][0])
        self.assertTrue('Project1' in workbook_path_mapping['Book2'])
        self.assertTrue('Project1/Project2' in workbook_path_mapping['Book2'])

    def test_parse_workbook_path_comma_separated(self):
        workbook_path_mapping = mv.parse_workbook_path(WORKBOOK_PATH_LIST_COMMA_SEPARATED)
        self.assertFalse('Book1' in workbook_path_mapping)
        self.assertFalse('Project1' in workbook_path_mapping['Book2'])

    def test_create_materialized_views_config(self):
        args = Mock()
        type(args).mode = "enable"
        type(args).materialize_now = False
        materialized_views_config = mv.create_materialized_views_config(args)

        self.assertEqual(2, len(materialized_views_config))
        self.assertTrue(materialized_views_config['materialized_views_enabled'])
        self.assertFalse(materialized_views_config['run_materialization_now'])

    def test_assert_site_options_valid(self):
        args = Mock()
        type(args).materialize_now = True
        self.assertFalse(mv.assert_site_options_valid(args))

        type(args).materialize_now = False
        type(args).mode = "enable"
        self.assertFalse(mv.assert_site_options_valid(args))

        type(args).materialize_now = False
        type(args).mode = "enable_all"
        self.assertTrue(mv.assert_site_options_valid(args))

    def test_assert_options_valid(self):
        args = Mock()
        type(args).type = "workbook"
        type(args).mode = "enable_all"
        self.assertFalse(mv.assert_options_valid(args))

        type(args).mode = None
        self.assertFalse(mv.assert_options_valid(args))

        type(args).type = "site"
        type(args).mode = "enable_all"
        self.assertTrue(mv.assert_options_valid(args))

    def test_assert_project_valid(self):
        project_name = "project_name"
        projects = []
        self.assertFalse(mv.assert_project_valid(project_name, projects))

        projects.append(project_name)
        self.assertTrue(mv.assert_project_valid(project_name, projects))



def create_test_projects():
    projects = {}
    for i in range(5):
        projects[str(i)] = Mock()
        type(projects[str(i)]).id = PropertyMock(return_value=str(i))
        type(projects[str(i)]).name = PropertyMock(return_value='project' + str(i))

    type(projects['0']).parent_id = PropertyMock(return_value=None)
    type(projects['1']).parent_id = PropertyMock(return_value='0')
    type(projects['2']).parent_id = PropertyMock(return_value='0')
    type(projects['3']).parent_id = PropertyMock(return_value='1')
    type(projects['4']).parent_id = PropertyMock(return_value='2')
    return projects
