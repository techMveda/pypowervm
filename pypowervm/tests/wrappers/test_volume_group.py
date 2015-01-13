# Copyright 2014, 2015 IBM Corp.
#
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import copy
import unittest

from pypowervm.tests.wrappers.util import pvmhttp
import pypowervm.wrappers.volume_group as vol_grp

VOL_GROUP_FILE = 'fake_volume_group.txt'


class TestVolumeGroup(unittest.TestCase):

    def setUp(self):
        super(TestVolumeGroup, self).setUp()
        self.vol_gr_resp = pvmhttp.load_pvm_resp(VOL_GROUP_FILE).get_response()
        self.vol_grp = vol_grp.VolumeGroup(self.vol_gr_resp.entry)

    def test_base(self):
        """Tests baseline function within the Volume Group."""
        self.assertEqual('image_pool', self.vol_grp.get_name())
        self.assertEqual(1063, self.vol_grp.get_capacity())
        self.assertEqual(1051, self.vol_grp.get_available_size())
        self.assertEqual(1051, self.vol_grp.get_free_space())
        self.assertEqual('00f8d6de00004b000000014a54555cd9',
                         self.vol_grp.get_serial_id())

    def test_vmedia_repos(self):
        """Tests the virtual media repositories."""
        repos = self.vol_grp.get_vmedia_repos()
        self.assertEqual(1, len(repos))
        self.assertEqual('VMLibrary', repos[0].get_name())
        self.assertEqual(11, repos[0].get_size())

        # Optical media
        vopts = repos[0].get_optical_media()
        self.assertEqual(2, len(vopts))

        self.assertEqual('blank_media1', vopts[0].get_media_name())
        self.assertEqual('0.0977', vopts[0].get_size())
        self.assertEqual('0eblank_media1', vopts[0].get_udid())
        self.assertEqual('rw', vopts[0].get_mount_type())

    def test_physical_volumes(self):
        """Tests the physical volumes in the VG."""
        pvs = self.vol_grp.get_phys_vols()
        self.assertEqual(1, len(pvs))

        pv = pvs[0]
        self.assertEqual('01MUlCTSAgICAgSVBSLTAgICA1RDgyODMwMDAwMDAwMDQw',
                         pv.get_udid())
        self.assertEqual(1089592, pv.get_capacity())
        self.assertEqual('hdisk1', pv.get_name())
        self.assertEqual('active', pv.get_state())
        self.assertEqual(False, pv.is_fc_backed())
        self.assertEqual('SAS RAID 0 Disk Array', pv.get_description())
        self.assertEqual('U78C9.001.WZS0095-P1-C14-R1-L405D828300-L0',
                         pv.get_loc_code())

    def test_virtual_disk(self):
        """Tests the virtual disk gets."""
        vdisks = self.vol_grp.get_virtual_disks()
        self.assertEqual(1, len(vdisks))

        vdisk = vdisks[0]
        self.assertEqual('asdf', vdisk.get_name())
        self.assertEqual('None', vdisk.get_label())
        self.assertEqual(1, vdisk.get_capacity())
        self.assertEqual('0300f8d6de00004b000000014a54555cd9.1',
                         vdisk.get_udid())

    def test_add_vdisk(self):
        """Performs a test flow that adds a virtual disk."""
        vdisks = self.vol_grp.get_virtual_disks()
        orig_vdisks = copy.copy(vdisks)

        self.assertEqual(1, len(vdisks))

        disk_elem = vol_grp.crt_virtual_disk_obj('disk_name', 10, 'label')
        disk = vol_grp.VirtualDisk(disk_elem)
        self.assertIsNotNone(disk)

        try:
            vdisks.append(disk)
            self.vol_grp.set_virtual_disks(vdisks)

            self.assertEqual(2, len(self.vol_grp.get_virtual_disks()))

            # make sure the second virt disk matches what we put in
            vdisk = self.vol_grp.get_virtual_disks()[1]
            self.assertEqual('disk_name', vdisk.get_name())
            self.assertEqual(10, vdisk.get_capacity())
            self.assertEqual('label', vdisk.get_label())
            self.assertEqual(None, vdisk.get_udid())
        finally:
            self.vol_grp.set_virtual_disks(orig_vdisks)
            self.assertEqual(1, len(self.vol_grp.get_virtual_disks()))

    def test_add_phys_vol(self):
        """Performs a test flow that adds a physical volume to the vol grp."""
        phys_vols = self.vol_grp.get_phys_vols()
        orig_pvols = copy.copy(phys_vols)

        self.assertEqual(1, len(phys_vols))

        phys_v = vol_grp.crt_phys_vol('disk1')
        phys_vol = vol_grp.PhysicalVolume(phys_v)
        self.assertIsNotNone(phys_vol)

        try:
            phys_vols.append(phys_vol)
            self.vol_grp.set_phys_vols(phys_vols)

            self.assertEqual(2, len(self.vol_grp.get_phys_vols()))

            # Make sure that the second physical volume matches
            pvol = self.vol_grp.get_phys_vols()[1]
            self.assertEqual('disk1', pvol.get_name())
        finally:
            self.vol_grp.set_phys_vols(orig_pvols)
            self.assertEqual(1, len(self.vol_grp.get_phys_vols()))

    def test_add_media_repo(self):
        """Performs a simple add to the volume group of a new media repo."""
        media_repos = self.vol_grp.get_vmedia_repos()
        orig_repos = copy.copy(media_repos)

        self.assertEqual(1, len(media_repos))

        vmedia_r = vol_grp.crt_vmedia_repo('repo', 10)
        vmedia_repo = vol_grp.VirtualOpticalMedia(vmedia_r)
        self.assertIsNotNone(vmedia_repo)

        try:
            media_repos.append(vmedia_repo)
            self.vol_grp.set_vmedia_repos(media_repos)

            self.assertEqual(2, len(self.vol_grp.get_vmedia_repos()))

            # Make sure that the second media repo matches
            repo = self.vol_grp.get_vmedia_repos()[1]
            self.assertEqual('repo', repo.get_name())
            self.assertEqual(10, repo.get_size())
            self.assertEqual(0, len(repo.get_optical_media()))

        finally:
            self.vol_grp.set_vmedia_repos(orig_repos)
            self.assertEqual(1, len(self.vol_grp.get_vmedia_repos()))

    def test_update_media_repo(self):
        """Performs a simple test to add optical media to an existing repo."""
        media_repos = self.vol_grp.get_vmedia_repos()

        vopt_medias = media_repos[0].get_optical_media()
        orig_vopt_medias = copy.copy(vopt_medias)
        self.assertEqual(2, len(vopt_medias))

        new_m = vol_grp.crt_voptical_media('name', '0.123', 'r')
        new_media = vol_grp.VirtualOpticalMedia(new_m)
        self.assertIsNotNone(new_media)

        try:
            vopt_medias.append(new_media)
            media_repos[0].set_optical_media(vopt_medias)
            self.assertEqual(3, len(media_repos[0].get_optical_media()))

            # Check the attributes
            media = media_repos[0].get_optical_media()[2]
            self.assertEqual('name', media.get_media_name())
            self.assertEqual('0.123', media.get_size())
            self.assertEqual('r', media.get_mount_type())

        finally:
            media_repos[0].set_optical_media(orig_vopt_medias)
            self.assertEqual(2, len(media_repos[0].get_optical_media()))