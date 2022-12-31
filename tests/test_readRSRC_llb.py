# -*- coding: utf-8 -*-

""" Test for pyLabview project, readRSRC script.

    This test extracts and then re-creates some RSRC files.
    Run it using `pytest` in project root folder.
"""

# Copyright (C) 2022 Mefistotelis <mefistotelis@gmail.com>
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

import filecmp
import os
import sys
import pathlib
import pytest
from unittest.mock import patch

# Import the functions to be tested
from pylabview.readRSRC import main as readRSRC_main

@pytest.mark.parametrize("rsrc_inp_fn", [
    os.path.join("examples", "lv14f1", "empty_vifile.vi"),
])
def test_readRSRC_repack_vi(rsrc_inp_fn):
    """ Test extraction and re-creation of VI/CTL/RSC files.

    VI files generated by the tool should be (with some exceptions, ie. older files which use
    random values for padding, or LLB files) same as original on binary level. Extracting and
    re-packing such file should result in receiving a binary-identical copy of the file.
    """
    # Only some files can be successfully tested in Python < 3.8, as XML parser was
    # improved in that version to preserve order of attributes.
    if sys.version_info < (3,8) and (
      rsrc_inp_fn.endswith("empty_vifile.vi")):
        pytest.skip("this file will not produce identical binary in python <= 3.8")

    rsrc_path, rsrc_filename = os.path.split(rsrc_inp_fn)
    rsrc_path = pathlib.Path(rsrc_path)
    rsrc_basename, rsrc_fileext = os.path.splitext(rsrc_filename)
    xml_fn = "{:s}.xml".format(rsrc_basename)
    if len(rsrc_path.parts) > 1:
        rsrc_out_path = os.sep.join(["test_out"] + list(rsrc_path.parts[1:]))
    else:
        rsrc_out_path = "test_out"
    rsrc_out_fn = os.sep.join([rsrc_out_path, "{:s}{:s}".format(rsrc_basename, rsrc_fileext)])
    single_vi_path_extr1 = os.sep.join([rsrc_out_path, "{:s}_extr1".format(rsrc_basename)])
    if not os.path.exists(single_vi_path_extr1):
        os.makedirs(single_vi_path_extr1)
    # Extract the VI file
    command = [os.path.join("pylabview", "readRSRC.py"), "-vv", "-x", "--keep-names", "-i", rsrc_inp_fn, "-m", os.sep.join([single_vi_path_extr1, xml_fn])]
    with patch.object(sys, 'argv', command):
        readRSRC_main()
    # Re-create the VI file
    command = [os.path.join("pylabview", "readRSRC.py"), "-vv", "-c", "-m", os.sep.join([single_vi_path_extr1, xml_fn]), "-i", rsrc_out_fn]
    with patch.object(sys, 'argv', command):
        readRSRC_main()
    # Compare repackaged file and the original
    match =  filecmp.cmp(rsrc_inp_fn, rsrc_out_fn, shallow=False)
    assert match, "Mismatched file: {:s}".format(rsrc_inp_fn)

#    os.path.join("examples", "lv14f1", "empty_libfile.llb"), -- currently fails because icon sections are re-ordered
@pytest.mark.parametrize("rsrc_inp_fn", [
    os.path.join("examples", "blank_project1_extr_from_exe_lv14f1.llb"),
])
def test_readRSRC_repack_llb(rsrc_inp_fn):
    """ Test extraction and re-creation of LLB files.

    LLB files generated by the tool are NOT the same as original on binary level. That is because
    names section generation has time dependencies (not to mention in some old versions of LV, the
    padding is often filled with random data). So instead of comparing LLBs, compare the extracted
    files from first extraction and second extraction.
    """
    rsrc_path, rsrc_filename = os.path.split(rsrc_inp_fn)
    rsrc_path = pathlib.Path(rsrc_path)
    rsrc_basename, rsrc_fileext = os.path.splitext(rsrc_filename)
    xml_fn = "{:s}.xml".format(rsrc_basename)
    if len(rsrc_path.parts) > 1:
        rsrc_out_path = os.sep.join(["test_out"] + list(rsrc_path.parts[1:]))
    else:
        rsrc_out_path = "test_out"
    rsrc_out_fn = os.sep.join([rsrc_out_path, "{:s}{:s}".format(rsrc_basename, rsrc_fileext)])
    single_vi_path_extr1 = os.sep.join([rsrc_out_path, "{:s}_extr1".format(rsrc_basename)])
    if not os.path.exists(single_vi_path_extr1):
        os.makedirs(single_vi_path_extr1)
    single_vi_path_extr2 = os.sep.join([rsrc_out_path, "{:s}_extr2".format(rsrc_basename)])
    if not os.path.exists(single_vi_path_extr2):
        os.makedirs(single_vi_path_extr2)
    # Extract the LLB file
    command = [os.path.join("pylabview", "readRSRC.py"), "-vv", "-x", "--keep-names", "-i", rsrc_inp_fn, "-m", os.sep.join([single_vi_path_extr1, xml_fn])]
    with patch.object(sys, 'argv', command):
        readRSRC_main()
    # Re-create the LLB file
    command = [os.path.join("pylabview", "readRSRC.py"), "-vv", "-c", "-m", os.sep.join([single_vi_path_extr1, xml_fn]), "-i", rsrc_out_fn]
    with patch.object(sys, 'argv', command):
        readRSRC_main()
    # Re-extract the LLB file
    command = [os.path.join("pylabview", "readRSRC.py"), "-vv", "-x", "--keep-names", "-i", rsrc_out_fn, "-m", os.sep.join([single_vi_path_extr2, xml_fn])]
    with patch.object(sys, 'argv', command):
        readRSRC_main()
    # Compare files from first extraction to the ones from second extraction
    dirs_cmp = filecmp.dircmp(single_vi_path_extr1, single_vi_path_extr2)
    assert len(dirs_cmp.left_only) == 0
    assert len(dirs_cmp.right_only) == 0
    assert len(dirs_cmp.funny_files) == 0
    (match, mismatch, errors) =  filecmp.cmpfiles(single_vi_path_extr1, single_vi_path_extr2, dirs_cmp.common_files, shallow=False)
    assert len(mismatch) == 0, "Mismatched files: {:s}".format(mismatch)
    assert len(errors) == 0, "Errors in files: {:s}".format(errors)
    # We should have an XML file and at least one extracted section file
    assert len(match) >= 2
