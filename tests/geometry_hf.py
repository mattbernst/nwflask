#!/usr/bin/env python
# -*- coding:utf-8 mode:python; tab-width:4; indent-tabs-mode:nil; py-indent-offset:4 -*-
##

"""
    geometry_hf
    ~~~~~~~~~~~~~~

    Test common Hartree-Fock implementations for geometry jobs.
"""
import unittest
import geoprep

class HFGeometryTestCase(unittest.TestCase):
    def test_extract_geometry_unchanged(self):
        #extract geometry from an energy job, which should be basically the
        #same as the input
        methane = self.G.make_fragment("C")
        methane.set_basis_name("3-21G")
        methane = geoprep.System([methane])
        job = self.C.make_energy_job(methane, "hf:rhf")
        job.run()

        reread = self.G.geolist_to_fragment(job.geometry)
        rmsd = self.G.align(methane.fragments[0], reread)["rmsd"]
        self.assertTrue(rmsd < 10**-5)

    def test_opt_rhf_water(self):
        #minimize geometry and verify that final structure has lower energy

        #without forcing lower symmetry, psi4 encounters a changed symmetry error
        #during optimization
        #TODO: the psi4 problem deserves its own test case
        options = {"symmetry" : "c1"}
        water = self.G.make_fragment("O")
        water.set_basis_name("3-21G")
        job = self.C.make_opt_job(water, "hf:rhf", options=options)
        job.run()

        self.assertTrue(len(job.geometry_history) > 1)
        
        first = self.G.geolist_to_fragment(job.geometry_history[0])
        first.set_basis_name("3-21G")
        job1 = self.C.make_energy_job(first, "hf:rhf", options=options)
        job1.run()

        self.assertTrue(job.energy < job1.energy)
        
