"""
<Program Name>
  test_replay_attack.py

<Author>
  Konstantin Andrianov

<Started>
  February 22, 2012

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Simulate a replay attack.  A simple client update vs. client update 
  implementing TUF.

  In the replay attack an attacker is able to trick clients into installing
  software that is older than that which the client previously knew to be
  available.

NOTE: The interposition provided by 'tuf.interposition' is used to intercept
all calls made by urllib/urillib2 to certain hostname specified in 
the interposition configuration file.  Look up interposition.py for more
information and illustration of a sample contents of the interposition 
configuration file.  Interposition was meant to make TUF integration with an
existing software updater an easy process.  This allows for more flexibility
to the existing software updater.  However, if you are planning to solely use
TUF there should be no need for interposition, all necessary calls will be
generated from within TUF.

Note: There is no difference between 'updates' and 'target' files.

"""

import os
import shutil
import urllib
import tempfile

import tuf.tests.system_tests.util_test_tools as util_test_tools
from tuf.interposition import urllib_tuf


class TestSetupError(Exception):
  pass



class ReplayAttackAlert(Exception):
  pass



def _download(url, filename, tuf=False):
  if tuf:
    urllib_tuf.urlretrieve(url, filename)
    
  else:
    urllib.urlretrieve(url, filename)





def test_replay_attack(TUF=False):
  """
  <Arguments>
    TUF:
      If set to 'False' all directories that start with 'tuf_' are ignored, 
      indicating that tuf is not implemented.

  <Purpose>
    Illustrate replay attack vulnerability.

  """

  ERROR_MSG = '\tReplay Attack was Successful!\n\n'


  try:
    # Setup.
    root_repo, url, server_proc, keyids = util_test_tools.init_repo(tuf=TUF)
    reg_repo = os.path.join(root_repo, 'reg_repo')
    tuf_repo = os.path.join(root_repo, 'tuf_repo')
    downloads = os.path.join(root_repo, 'downloads')
    tuf_targets = os.path.join(tuf_repo, 'targets')

    # Add file to 'repo' directory: {root_repo}
    filepath = util_test_tools.add_file_to_repository(reg_repo, 'Test A')
    file_basename = os.path.basename(filepath)
    url_to_repo = url+'reg_repo/'+file_basename
    downloaded_file = os.path.join(downloads, file_basename)

    # Attacker saves the original file into 'evil_dir'.
    evil_dir = tempfile.mkdtemp(dir=root_repo)
    vulnerable_file = os.path.join(evil_dir, file_basename)
    shutil.copy(filepath, evil_dir)

    if TUF:
      print 'TUF ...'

      # Update TUF metadata before attacker modifies anything.
      util_test_tools.tuf_refresh_repo(root_repo, keyids)

      # Modify the url.  Remember that the interposition will intercept 
      # urls that have 'localhost:9999' hostname, which was specified in
      # the json interposition configuration file.  Look for 'hostname'
      # in 'util_test_tools.py'. Further, the 'file_basename' is the target
      # path relative to 'targets_dir'. 
      url_to_repo = 'http://localhost:9999/'+file_basename

    # End of Setup.


    # Client performs initial update.
    _download(url=url_to_repo, filename=downloaded_file, tuf=TUF)

    # Downloads are stored in the same directory '{root_repo}/downloads/'
    # for regular and tuf clients.
    downloaded_content = util_test_tools.read_file_content(downloaded_file)
    if 'Test A' != downloaded_content:
      raise TestSetupError('[Initial Updata] Failed to download the file.')

    # Developer patches the file and updates the repository.
    util_test_tools.modify_file_at_repository(filepath, 'Test NOT A')

    # Updating tuf repository.  This will copy files from regular repository
    # into tuf repository and refresh the metadata
    if TUF:
      util_test_tools.tuf_refresh_repo(root_repo, keyids)


    # Client downloads the patched file.
    _download(url=url_to_repo, filename=downloaded_file, tuf=TUF)

    # Content of the downloaded file.
    downloaded_content = util_test_tools.read_file_content(downloaded_file)
    if 'Test NOT A' != downloaded_content:
      raise TestSetupError('[Update] Failed to update the file.')

    # Attacker tries to be clever, he manages to modifies regular and tuf 
    # targets directory by replacing a patched file with an old one.
    if os.path.isdir(tuf_targets):
      target = os.path.join(tuf_targets, file_basename)
      util_test_tools.delete_file_at_repository(target)
      shutil.copy(vulnerable_file, tuf_targets)
      # Verify that 'target' is an old, un-patched file.
      target = os.path.join(tuf_targets, file_basename)
      target_content = util_test_tools.read_file_content(target)
      if 'Test A' != target_content:
        raise TestSetupError("The 'target' file contains new data!")

    else:
      util_test_tools.delete_file_at_repository(filepath)
      shutil.copy(vulnerable_file, reg_repo)


    # Client downloads the file once more.
    _download(url=url_to_repo, filename=downloaded_file, tuf=TUF)

    # Check whether the attack succeeded by inspecting the content of the
    # update.  The update should contain 'Test NOT A'.
    downloaded_content = util_test_tools.read_file_content(downloaded_file)
    if 'Test NOT A' != downloaded_content:
      raise ReplayAttackAlert(ERROR_MSG)


  finally:
    util_test_tools.cleanup(root_repo, server_proc)





try:
  test_replay_attack(TUF=False)
except ReplayAttackAlert, error:
  print error



try:
  test_replay_attack(TUF=True)
except ReplayAttackAlert, error:
  print error
