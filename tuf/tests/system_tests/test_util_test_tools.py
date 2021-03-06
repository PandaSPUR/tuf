"""
<Program Name>
  test_util_test_tools.py

<Author>
  Konstantin Andrianov

<Started>
  February 26, 2012

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test util_test_tools.

"""
import os
import urllib
import unittest
import util_test_tools



class test_UtilTestTools(unittest.TestCase):
  def setUp(self):
    unittest.TestCase.setUp(self)

    # Unpacking necessary parameters returned from init_repo()
    essential_params = util_test_tools.init_repo(tuf=True)
    self.root_repo = essential_params[0] 
    self.url = essential_params[1]
    self.server_proc = essential_params[2]
    self.keyids = essential_params[3]
    # TODO: In the line below, 'util_test_tools.init_repo' does
    # not return the interposition config and this unit test
    # does not directly use it.  WIP? 
    #self.interpose_json = essential_params[4] 

  def tearDown(self):
    unittest.TestCase.tearDown(self)
    util_test_tools.cleanup(self.root_repo, self.server_proc)


#================================================#
#  Below are few quick tests to make sure that  #
#  everything works smoothly in util_test_tools. #
#================================================#

  # A few quick internal tests to see if everything runs smoothly.
  def test_direct_download(self):
    # Setup.
    reg_repo = os.path.join(self.root_repo, 'reg_repo')
    downloads = os.path.join(self.root_repo, 'downloads')
    filepath = util_test_tools.add_file_to_repository(reg_repo, 'Test')
    file_basename = os.path.basename(filepath)
    url_to_reg_repo = self.url+'reg_repo/'+file_basename
    downloaded_file = os.path.join(downloads, file_basename)

    # Test direct download using 'urllib.urlretrieve'.
    urllib.urlretrieve(url_to_reg_repo, downloaded_file)
    self.assertTrue(os.path.isfile(downloaded_file))

    # Verify the content of the downloaded file.
    downloaded_content = util_test_tools.read_file_content(downloaded_file)
    self.assertEquals('Test', downloaded_content)





  def test_correct_directory_structure(self):
    # Verify following directories exists: '{root_repo}/reg_repo/',
    # '{root_repo}/downloads/.
    self.assertTrue(os.path.isdir(os.path.join(self.root_repo, 'reg_repo')))
    self.assertTrue(os.path.isdir(os.path.join(self.root_repo, 'downloads')))

    # Verify that all necessary TUF-paths exist.
    tuf_repo = os.path.join(self.root_repo, 'tuf_repo')
    tuf_client = os.path.join(self.root_repo, 'tuf_client')
    metadata_dir = os.path.join(tuf_repo, 'metadata')
    current_dir = os.path.join(tuf_client, 'metadata', 'current')

    # Verify '{root_repo}/tuf_repo/metadata/role.txt' paths exists.
    for role in ['root', 'targets', 'release', 'timestamp']:
      # Repository side.
      role_file = os.path.join(metadata_dir, role+'.txt')
      self.assertTrue(os.path.isfile(role_file))

      # Client side.
      role_file = os.path.join(current_dir, role+'.txt')
      self.assertTrue(os.path.isfile(role_file))

    # Verify '{root_repo}/tuf_repo/keystore/keyid.key' exists.
    keys_list = os.listdir(os.path.join(tuf_repo, 'keystore'))
    self.assertEquals(len(keys_list), 1)

    # Verify '{root_repo}/tuf_repo/targets/' directory exists.
    self.assertTrue(os.path.isdir(os.path.join(tuf_repo, 'targets')))





  def test_methods(self):
    """
    Making sure following methods work as intended:
    - add_file_to_repository(data)
    - modify_file_at_repository(filepath, data)
    - delete_file_at_repository(filepath)
    - read_file_content(filepath)
    - tuf_refresh_repo()
    - tuf_refresh_and_download()

    Note: here file at the 'filepath' and the 'target' file at tuf-targets
    directory are identical files.
    Ex: filepath = '{root_repo}/reg_repo/file.txt'
        target = '{root_repo}/tuf_repo/targets/file.txt'
    """

    reg_repo = os.path.join(self.root_repo, 'reg_repo')
    tuf_repo = os.path.join(self.root_repo, 'tuf_repo')
    downloads = os.path.join(self.root_repo, 'downloads')

    # Test 'add_file_to_repository(directory, data)' and
    # read_file_content(filepath) methods.
    filepath = util_test_tools.add_file_to_repository(reg_repo, 'Test')
    self.assertTrue(os.path.isfile(filepath))
    self.assertEquals(os.path.dirname(filepath), reg_repo)
    filepath_content = util_test_tools.read_file_content(filepath)
    self.assertEquals('Test', filepath_content)

    # Test 'modify_file_at_repository(filepath, data)' method.
    filepath = util_test_tools.modify_file_at_repository(filepath, 'Modify')
    self.assertTrue(os.path.exists(filepath))
    filepath_content = util_test_tools.read_file_content(filepath)
    self.assertEquals('Modify', filepath_content)

    # Test 'tuf_refresh_repo' method.
    util_test_tools.tuf_refresh_repo(self.root_repo, self.keyids)
    file_basename = os.path.basename(filepath)
    target = os.path.join(tuf_repo, 'targets', file_basename)
    self.assertTrue(os.path.isfile(target))

    # Test 'delete_file_at_repository(filepath)' method.
    util_test_tools.delete_file_at_repository(filepath)
    self.assertFalse(os.path.exists(filepath))

    # Test 'tuf_refresh_repo' method once more.
    util_test_tools.tuf_refresh_repo(self.root_repo, self.keyids)
    file_basename = os.path.basename(filepath)
    target = os.path.join(tuf_repo, 'targets', file_basename)
    self.assertFalse(os.path.isfile(target))




if __name__ == '__main__':
  unittest.main()
