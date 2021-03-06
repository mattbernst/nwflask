#!/usr/bin/env python
# -*- coding:utf-8 mode:python; tab-width:4; indent-tabs-mode:nil; py-indent-offset:4 -*-
##

"""
    reference_values
    ~~~~~~~~~~~~~~

    Keep reference values for cross-package comparisons in one location, as
    opposed to repeating literals across test files.
"""
#these energies use the unoptimized geometry generated by pybel make3d
#all values are hartrees
methane_rhf_321g = -39.9766425
methyl_uhf_ccpvdz = -39.5638132
methyl_rohf_ccpvdz = -39.5596229
hcl_rhf_ccpvdz = -460.0889424
hcl_rhf_631gs = -460.0589984

#energy from external geometry
methanol_rhf_321g = -114.39179686
methanol_rhf_g3mp2large = -115.0850089

#semiempirical heats of formation (also in hartrees)
phenyl_rohf_pm3_hof = 0.126826
phenyl_uhf_pm3_hof = 0.119951
methyl_rohf_pm3_hof = 0.047725
methyl_uhf_pm3_hof = 0.044800
methylium_pm3_hof = 0.408868
carbanide_pm3_hof = 0.082962
methane_pm3_hof = -0.020660
methane_mndo_hof = -0.018578
methane_am1_hof = -0.012894
methane_rm1_hof = -0.022059
methane_mindo3_hof = -0.009680
methane_pm6_hof = -0.019537
methane_pddgmndo_hof = -0.026589
methane_pddgpm3_hof = -0.025640
methane_am1dphot_hof = -0.002390
